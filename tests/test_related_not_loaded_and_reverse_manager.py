"""
Regression tests for the v1.3.0 ForeignKey relation hardening:

1. An unhydrated ForeignKey/OneToOneField attribute reads as a
   `RelatedNotLoaded` sentinel (not a raw scalar, not the hydrated model) --
   cheap ops (.pk, bool(), ==) work without a query; anything else raises
   `RelatedNotLoadedFault`.
2. `Model.related()`'s forward branch caches the hydrated instance in place
   so subsequent bare attribute access is instant; its reverse branch is an
   O(1) lookup via `_reverse_relation_map()` instead of a per-call linear
   scan, and returns a single instance (not a list) for a OneToOneField's
   reverse side.
3. `Model.related_manager()` returns a lazy, chainable manager over a
   reverse relation.
4. Assigning the wrong model type to a ForeignKey raises
   `RelatedTypeMismatchFault`; colliding `related_name`s raise
   `RelatedNameConflictFault`.
5. The admin's `format_value()` renders an unhydrated FK without crashing.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from aquilia.admin.options import ModelAdmin
from aquilia.db.engine import configure_database
from aquilia.faults.domains import RelatedNameConflictFault, RelatedNotLoadedFault, RelatedTypeMismatchFault
from aquilia.models.base import Model, ModelRegistry
from aquilia.models.deletion import CASCADE, SET_NULL
from aquilia.models.fields_module import AutoField, CharField, ForeignKey, OneToOneField
from aquilia.models.relations import RelatedNotLoaded


class RnlAuthor(Model):
    # Deliberately unique names -- ModelRegistry / reverse-relation caches
    # are process-wide singletons shared with every other test module.
    table = "rnl_author"
    id = AutoField(primary_key=True)
    name = CharField(max_length=50)


class RnlBook(Model):
    table = "rnl_book"
    id = AutoField(primary_key=True)
    title = CharField(max_length=100)
    author = ForeignKey(RnlAuthor, related_name="books", on_delete=CASCADE)
    editor = ForeignKey(RnlAuthor, null=True, related_name="edited_books", on_delete=SET_NULL)


class RnlProfile(Model):
    table = "rnl_profile"
    id = AutoField(primary_key=True)
    bio = CharField(max_length=200)
    author = OneToOneField(RnlAuthor, related_name="profile")


# Dedicated, otherwise-unused target + two colliding referencing models --
# isolated on purpose so the deliberately-broken reverse-relation map these
# create can't poison _reverse_relation_map() for RnlAuthor (used by every
# other test in this file) regardless of test execution order.
class RnlConflictTarget(Model):
    table = "rnl_conflict_target"
    id = AutoField(primary_key=True)


class RnlConflictA(Model):
    table = "rnl_conflict_a"
    id = AutoField(primary_key=True)
    target = ForeignKey(RnlConflictTarget, related_name="clashing", on_delete=CASCADE)


class RnlConflictB(Model):
    table = "rnl_conflict_b"
    id = AutoField(primary_key=True)
    target = ForeignKey(RnlConflictTarget, related_name="clashing", on_delete=CASCADE)


@pytest_asyncio.fixture
async def seeded_db():
    database = configure_database("sqlite:///:memory:", alias="default")
    await database.connect()

    models = (RnlAuthor, RnlBook, RnlProfile)
    for model in models:
        ModelRegistry.register(model)
        model._reverse_fk_cache = None
        model._reverse_relation_cache = None

    originals = {}
    for model in models:
        originals[model] = model._db
        model._db = database
        await database.execute(model.generate_create_table_sql())

    await database.execute("INSERT INTO rnl_author (id, name) VALUES (1, 'Alice')")
    await database.execute("INSERT INTO rnl_author (id, name) VALUES (2, 'Bob')")
    await database.execute("INSERT INTO rnl_book (id, title, author_id, editor_id) VALUES (1, 'Book A', 1, NULL)")
    await database.execute("INSERT INTO rnl_book (id, title, author_id, editor_id) VALUES (2, 'Book B', 1, 2)")
    await database.execute("INSERT INTO rnl_profile (id, bio, author_id) VALUES (1, 'Bio of Alice', 1)")

    yield database

    for model, original in originals.items():
        model._db = original
    await database.disconnect()


class TestRelatedNotLoadedSentinel:
    async def test_unhydrated_fk_is_sentinel(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        assert isinstance(book.author, RelatedNotLoaded)

    async def test_sentinel_pk_no_query(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        assert book.author.pk == 1
        assert book.author.id == 1

    async def test_sentinel_bool(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        assert bool(book.author) is True

    async def test_null_fk_is_none_not_sentinel(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        assert book.editor is None

    async def test_sentinel_eq_against_hydrated_instance(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        alice = await RnlAuthor.get(pk=1)
        assert book.author == alice
        assert alice == book.author  # symmetric via Model.__eq__ NotImplemented fallback

    async def test_sentinel_eq_against_raw_pk(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        assert book.author == 1
        assert book.author != 2

    async def test_other_attribute_access_raises(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        with pytest.raises(RelatedNotLoadedFault):
            _ = book.author.name

    async def test_fault_is_also_attribute_error(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        with pytest.raises(AttributeError):
            _ = book.author.name

    async def test_hasattr_degrades_gracefully(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        assert hasattr(book.author, "name") is False


class TestRelatedForwardCaching:
    async def test_related_hydrates_and_caches(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        assert isinstance(book.author, RelatedNotLoaded)

        resolved = await book.related("author")
        assert isinstance(resolved, RnlAuthor)
        assert resolved.name == "Alice"

        # Bare attribute access afterward is the cached, hydrated instance --
        # not the sentinel, no further query needed.
        assert isinstance(book.author, RnlAuthor)
        assert book.author is resolved

    async def test_related_zero_query_when_already_hydrated(self, seeded_db):
        book = await RnlBook.objects.select_related("author").filter(title="Book A").first()
        assert isinstance(book.author, RnlAuthor)

        # related() on an already-hydrated attribute must be a zero-query
        # fast path returning the same instance, not re-fetching.
        again = await book.related("author")
        assert again is book.author


class TestReverseRelations:
    async def test_related_reverse_returns_list_for_plain_fk(self, seeded_db):
        alice = await RnlAuthor.get(pk=1)
        books = await alice.related("books")
        assert isinstance(books, list)
        assert {b.title for b in books} == {"Book A", "Book B"}

    async def test_reverse_relation_map_has_default_and_explicit_names(self, seeded_db):
        alice = await RnlAuthor.get(pk=1)
        mapping = alice._reverse_relation_map()
        assert "books" in mapping  # explicit related_name on RnlBook.author
        assert "profile" in mapping  # explicit related_name on RnlProfile.author

    async def test_related_manager_lazy_chaining(self, seeded_db):
        alice = await RnlAuthor.get(pk=1)
        count = await alice.related_manager("books").filter(title="Book A").count()
        assert count == 1

    async def test_related_manager_returns_related_manager_type(self, seeded_db):
        from aquilia.models.manager import RelatedManager

        alice = await RnlAuthor.get(pk=1)
        mgr = alice.related_manager("books")
        assert isinstance(mgr, RelatedManager)

    async def test_one_to_one_reverse_returns_single_instance(self, seeded_db):
        alice = await RnlAuthor.get(pk=1)
        profile = await alice.related("profile")
        assert isinstance(profile, RnlProfile)
        assert profile.bio == "Bio of Alice"

    async def test_one_to_one_reverse_none_when_missing(self, seeded_db):
        bob = await RnlAuthor.get(pk=2)
        profile = await bob.related("profile")
        assert profile is None


class TestTypeSafeAssignment:
    async def test_wrong_model_assignment_raises(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()

        new_book = RnlBook(title="Mismatch")
        new_book.author = book  # wrong type: RnlBook, not RnlAuthor
        with pytest.raises(RelatedTypeMismatchFault):
            new_book.full_clean()

    async def test_correct_model_assignment_still_works(self, seeded_db):
        alice = await RnlAuthor.get(pk=1)

        new_book = RnlBook(title="Fine")
        new_book.author = alice
        new_book.full_clean()  # must not raise


class TestRelatedNameConflict:
    def test_colliding_related_name_raises(self):
        ModelRegistry.register(RnlConflictTarget)
        ModelRegistry.register(RnlConflictA)
        ModelRegistry.register(RnlConflictB)
        RnlConflictTarget._reverse_relation_cache = None

        with pytest.raises(RelatedNameConflictFault):
            RnlConflictTarget._reverse_relation_map()


class TestAdminRendersUnloadedFK:
    async def test_format_value_does_not_crash(self, seeded_db):
        admin = ModelAdmin(model=RnlBook)
        book = await RnlBook.objects.filter(id=1).first()

        rendered = admin.format_value("author", book.author)
        assert "RelatedNotLoaded" in rendered


class TestForeignKeyDescriptor:
    """
    ForeignKey/OneToOneField are real data descriptors (define __get__ and
    __set__) so a static checker can resolve `instance.author` to
    `RnlAuthor | RelatedNotLoaded[RnlAuthor] | None` instead of the bare
    `ForeignKey` field object -- see aquilia/models/relations.py `Related`
    and aquilia/models/fields_module.py `ForeignKey.__get__`. This class
    covers the runtime contract of that descriptor: class-level access must
    still return the Field object (needed by introspection, the query
    builder, and admin/migration code that does `Model.author.related_model`
    etc.), while instance-level access/assignment behaves exactly as before
    the descriptor was added.
    """

    def test_class_level_access_returns_field_object(self):
        # Model.author (no instance) must return the ForeignKey descriptor
        # itself, not None/AttributeError -- e.g. RnlBook.author.related_model
        # is used throughout the ORM (SQL generation, introspection, admin).
        field = RnlBook.author
        assert isinstance(field, ForeignKey)
        assert field.related_model is RnlAuthor

    async def test_instance_level_get_set_roundtrip(self, seeded_db):
        alice = await RnlAuthor.get(pk=1)
        book = RnlBook(title="Descriptor Roundtrip")
        book.author = alice
        assert book.author is alice

    async def test_instance_access_after_hydration_is_not_sentinel(self, seeded_db):
        # Filtering on "title" (not "id") to sidestep the pre-existing,
        # separately-documented "ambiguous column name" issue with
        # select_related() + filter() on a column name shared by both
        # tables (see CHANGELOG.md [1.3.0b0] Known Issues).
        book = await RnlBook.objects.select_related("author").filter(title="Book A").first()
        assert isinstance(book.author, RnlAuthor)

    async def test_instance_access_before_hydration_is_sentinel(self, seeded_db):
        book = await RnlBook.objects.filter(id=1).first()
        assert isinstance(book.author, RelatedNotLoaded)
