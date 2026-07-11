from typing import Annotated, Literal

from aquilia.contracts import Contract, ContractUnion, Facet


def test_sigil_content_hash():
    class SimpleBP(Contract):
        name: str
        age: int

    class SimpleBP2(Contract):
        name: str
        age: int

    class DiffBP(Contract):
        name: str
        age: float  # changed type

    assert SimpleBP._sigil.content_hash == SimpleBP2._sigil.content_hash
    assert SimpleBP._sigil.content_hash != DiffBP._sigil.content_hash


def test_sigil_diff():
    class BaseBP(Contract):
        name: str
        age: int

    class NewBP(Contract):
        name: str
        email: str
        age: float

    diff = BaseBP._sigil.diff(NewBP._sigil)
    assert "email" in diff.added_fields
    assert "age" in diff.changed_fields
    assert diff.breaking is True  # because age type changed from int to float


def test_contract_union_dispatch_literal():
    class Circle(Contract):
        type: Literal["circle"]
        radius: float

    class Square(Contract):
        type: Literal["square"]
        side: float

    Shape = Circle | Square

    assert isinstance(Shape, ContractUnion)

    # Test Circle validation
    errors, val = Shape.validate({"type": "circle", "radius": 5.0})
    assert not errors
    assert val["type"] == "circle"
    assert val["radius"] == 5.0

    # Test Square validation
    errors, val = Shape.validate({"type": "square", "side": 4.0})
    assert not errors
    assert val["type"] == "square"
    assert val["side"] == 4.0

    # Test unknown dispatch type
    errors, val = Shape.validate({"type": "triangle", "base": 3.0})
    assert errors
    assert "__all__" in errors or "type" in errors


def test_contract_union_dispatch_discriminator():
    class Dog(Contract):
        class Spec:
            discriminator = "kind"

        kind: str
        bark_volume: int

    class Cat(Contract):
        class Spec:
            discriminator = "kind"

        kind: str
        purr_frequency: float

    Animal = Dog | Cat
    assert isinstance(Animal, ContractUnion)

    errors, val = Animal.validate({"kind": "Dog", "bark_volume": 11})
    assert not errors
    assert val["kind"] == "Dog"
    assert val["bark_volume"] == 11


def test_contract_revision_migration():
    class V1(Contract):
        class Spec:
            revision = 1

        username: str

    class V2(Contract):
        class Spec:
            revision = 2
            migrate_from = V1

        email: str

        @classmethod
        def migrate_step(cls, data: dict, from_rev: int) -> dict:
            if from_rev == 1:
                data["email"] = f"{data.pop('username')}@example.com"
            return data

    # Test direct migration when V2 is passed data from V1 schema
    # (i.e. username is provided instead of email)
    # V2 requires "email", so if migration doesn't run it will fail.
    errors, validated = V2._sigil.validate({"username": "ada"})
    assert not errors
    assert validated["email"] == "ada@example.com"


def test_new_facets_and_pipeline_schema_merging():
    from aquilia.contracts.transforms import dasherize, lower, strip

    class ArticleContract(Contract):
        slug: Annotated[str, Facet.text() >> strip >> lower >> dasherize >> Facet.pattern(r"^[a-z0-9-]+$")]
        author_email: Annotated[str, Facet.email()]
        website: Annotated[str, Facet.url()]

    # Verify that Facet proxy methods created correct facets
    assert ArticleContract.get_facet("slug") is not None
    assert ArticleContract.get_facet("author_email") is not None
    assert ArticleContract.get_facet("website") is not None

    # Test pipeline execution
    ok = ArticleContract(
        data={"slug": "  My Great SLUG  ", "author_email": "test@example.com", "website": "https://example.com"}
    )
    assert ok.is_sealed() is True
    assert ok.validated_data["slug"] == "my-great-slug"

    # Verify pipeline schema merging
    sch = ArticleContract.to_schema()
    slug_sch = sch["properties"]["slug"]
    assert slug_sch["type"] == "string"
    assert slug_sch["pattern"] == "^[a-z0-9-]+$"
