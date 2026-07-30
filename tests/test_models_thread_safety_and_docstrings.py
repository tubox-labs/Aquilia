"""
Unit and concurrency tests for aquilia.models thread-safety, descriptor binding, and cache invalidation.
"""

import threading

from aquilia.models import CharField, ForeignKey, Model, ModelRegistry


class TestModelsThreadSafetyAndRegistry:
    """Test suite verifying thread safety and cache invalidation in aquilia/models."""

    def test_concurrent_registry_access(self):
        """Verify concurrent register, get, and reset calls on ModelRegistry do not raise race conditions."""
        errors = []

        def worker(idx: int):
            try:
                class DynamicModel(Model):
                    name = CharField(max_length=50)

                DynamicModel.__name__ = f"DynamicModel_{idx}"

                ModelRegistry.register(DynamicModel)
                retrieved = ModelRegistry.get(f"DynamicModel_{idx}")
                assert retrieved is DynamicModel or retrieved is None
                _ = ModelRegistry.all_models()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent registry access produced errors: {errors}"
        ModelRegistry.reset()

    def test_concurrent_subclass_manager_descriptor(self):
        """Verify accessing inherited manager on multiple subclasses concurrently is thread-safe."""
        class BaseEntity(Model):
            table = "base_entities"
            abstract = True
            name = CharField(max_length=100)

        class UserEntity(BaseEntity):
            table = "user_entities"

        class ProductEntity(BaseEntity):
            table = "product_entities"

        errors = []

        def access_user():
            try:
                for _ in range(100):
                    mgr = UserEntity.objects
                    assert mgr._model_cls is UserEntity
            except Exception as exc:
                errors.append(exc)

        def access_product():
            try:
                for _ in range(100):
                    mgr = ProductEntity.objects
                    assert mgr._model_cls is ProductEntity
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=access_user)
        t2 = threading.Thread(target=access_product)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert not errors, f"Concurrent manager descriptor access produced errors: {errors}"

    def test_reverse_relation_cache_invalidation(self):
        """Verify registering a new model invalidates stale reverse relation caches on existing models."""
        ModelRegistry.reset()

        class Parent(Model):
            name = CharField(max_length=50)

        # Populate reverse relation cache on Parent
        _ = Parent._get_reverse_fk_refs()
        assert Parent._reverse_fk_cache is not None

        # Register child pointing to Parent
        class Child(Model):
            parent = ForeignKey(Parent, related_name="children")

        # Registration should have invalidated Parent's cached reverse relations
        assert Parent._reverse_fk_cache is None
        assert Parent._reverse_relation_cache is None

        # Re-fetching should now discover Child
        refs = Parent._get_reverse_fk_refs()
        assert any(ref[0] is Child for ref in refs)

        ModelRegistry.reset()
