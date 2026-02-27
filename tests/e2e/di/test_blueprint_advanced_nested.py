from __future__ import annotations
import pytest
from typing import Union
from aquilia.blueprints import Blueprint, Field

# ── Self-Referential / Lazy Blueprints ───────────────────────────────────

class TreeNode(Blueprint):
    id: int
    name: str
    parent: TreeNode | None = None
    children: list[TreeNode] = Field(default_factory=list)

def test_lazy_blueprint_self_referential():
    """Test that a Blueprint can reference itself (tree structure)."""
    data = {
        "id": 1,
        "name": "Root",
        "parent": None,
        "children": [
            {
                "id": 2,
                "name": "Child 1",
                "parent": {"id": 1, "name": "Root"},
                "children": []
            },
            {
                "id": 3,
                "name": "Child 2",
                "children": [
                    {"id": 4, "name": "Grandchild"}
                ]
            }
        ]
    }
    
    bp = TreeNode(data=data)
    assert bp.is_sealed() is True
    
    vd = bp.validated_data
    assert vd.id == 1
    assert len(vd.children) == 2
    assert vd.children[0].id == 2
    assert vd.children[0].parent.id == 1
    assert vd.children[1].children[0].name == "Grandchild"

def test_lazy_blueprint_validation_errors():
    """Test that errors deep in a recursive structure propagate up."""
    data = {
        "id": 1,
        "name": "Root",
        "children": [
            {"id": "not-an-int", "name": "Bad Child"}
        ]
    }
    
    bp = TreeNode(data=data)
    assert bp.is_sealed() is False
    assert "children" in bp.errors
    # Should say something about children[0] failing cast
    assert any("not-an-int" in str(e) or "Expected integer" in str(e) for e in bp.errors["children"])


# ── Nested Dicts ────────────────────────────────────────────────────────

class AppConfig(Blueprint):
    version: str
    features: dict[str, bool]

class ServerConfig(Blueprint):
    host: str
    port: int
    apps: dict[str, AppConfig]

def test_nested_dict_success():
    """Test deeply nested dicts with strong value types."""
    data = {
        "host": "localhost",
        "port": 8080,
        "apps": {
            "auth": {"version": "1.0", "features": {"sso": True, "mfa": False}},
            "billing": {"version": "2.1", "features": {"stripe": True}}
        }
    }
    
    bp = ServerConfig(data=data)
    assert bp.is_sealed() is True
    
    vd = bp.validated_data
    assert vd.apps["auth"].version == "1.0"
    assert vd.apps["auth"].features["sso"] is True

def test_nested_dict_failure():
    """Test dict value validation failure propagation."""
    data = {
        "host": "localhost",
        "port": 8080,
        "apps": {
            "auth": {"version": "1.0", "features": {"sso": True}},
            "billing": {"version": "2.1", "features": "invalid-features"}  # Should be dict
        }
    }
    
    bp = ServerConfig(data=data)
    assert bp.is_sealed() is False
    assert "apps" in bp.errors
    # The error should indicate that 'apps[billing]' failed
    err_str = str(bp.errors["apps"])
    assert "billing" in err_str


# ── Polymorphic Unions ──────────────────────────────────────────────────

class Dog(Blueprint):
    bark_volume: int

class Cat(Blueprint):
    meow_pitch: float

class PetOwner(Blueprint):
    name: str
    pet: Union[Dog, Cat]

class MultiPetOwner(Blueprint):
    name: str
    pets: list[Dog | Cat]

def test_polymorphic_union_success():
    """Test that Union resolves to the first matching Blueprint."""
    bp1 = PetOwner(data={"name": "Alice", "pet": {"bark_volume": 80}})
    assert bp1.is_sealed() is True
    assert bp1.validated_data.pet.bark_volume == 80

    bp2 = PetOwner(data={"name": "Bob", "pet": {"meow_pitch": 440.5}})
    assert bp2.is_sealed() is True
    assert bp2.validated_data.pet.meow_pitch == 440.5

def test_polymorphic_union_failure():
    """Test that Union fails properly if no Blueprint matches."""
    bp = PetOwner(data={"name": "Charlie", "pet": {"scales": True}})
    assert bp.is_sealed() is False
    assert "pet" in bp.errors
    err_str = str(bp.errors["pet"][0])
    assert "did not match any polymorphic schema" in err_str
    assert "bark_volume" in err_str
    assert "meow_pitch" in err_str

def test_polymorphic_list():
    """Test list of polymorphic unions."""
    bp = MultiPetOwner(data={
        "name": "Zoo",
        "pets": [
            {"bark_volume": 50},
            {"meow_pitch": 800.0},
            {"bark_volume": 100}
        ]
    })
    
    assert bp.is_sealed() is True
    assert len(bp.validated_data.pets) == 3
    assert getattr(bp.validated_data.pets[0], "bark_volume") == 50
    assert getattr(bp.validated_data.pets[1], "meow_pitch") == 800.0
