---
title: "Projections"
description: "Declaring and using named subsets of fields for dynamic schema tailoring"
icon: lucide/eye
---Projections allow you to declare and use named subsets of fields (facets) on a [Blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L826-L2075), enabling dynamic tailoring of output schemas without duplicating blueprint definitions.

---

### 1. What is a Projection?

A **Projection** is a named subset of facets, acting like a database view or a SQL `SELECT` projection over a model ([projections.py:L4-L6](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L4-L6)).

Instead of repeating lists of fields (e.g., `fields = [...]`) in different serializers or route definitions, projections let you define field lists once in the blueprint's specifications and select them dynamically by name at the route or controller level ([projections.py:L4-L6](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L4-L6)). The concept is named "Projection" because it projects a subset of the model's facets onto the serialized output ([projections.py:L8-L11](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L8-L11)).

---

### 2. Defining Projections in `Spec.projections`

Projections are declared within the `Spec` inner class of a [Blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L826-L2075) class ([projections.py:L30-L38](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L30-L38)). The configurations are mapped via a dictionary:

```python
class Spec:
    model = Product
    projections = {
        "summary": ["id", "name", "price"],
        "detail": ["id", "name", "description", "price", "category"],
        "admin": "__all__",
    }
```

The dictionary maps the projection name (e.g., `"summary"`) to either:
- A list/tuple of facet names ([projections.py:L88](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L88)).
- Special reserve keywords like `"__all__"` or `"__minimal__"` ([projections.py:L41-L43](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L41-L43)).
- A single field name string ([projections.py:L106-L107](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L106-L107)).

---

### 3. Special Values: `"__all__"` and `"__minimal__"`

Aquilia supports two reserved values for projections:

#### `"__all__"`
Resolves to all non-write-only facets ([projections.py:L42](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L42)). During configuration, the registry resolves this by computing the set difference between all facet names and write-only facet names ([projections.py:L74](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L74), [projections.py:L83-L84](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L83-L84)).

#### `"__minimal__"`
Resolves to only the primary key (PK) and read-only facets ([projections.py:L43](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L43)). Inside the registry's configuration phase, it is mapped to a placeholder empty frozenset ([projections.py:L85-L87](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L85-L87)) and is fully resolved downstream by the [Blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L826-L2075) class itself.

---

### 4. Exclusion Syntax: `"-field_name"` Prefix

Instead of explicitly listing all fields to include, projections can define which fields to exclude by prefixing the facet name with a minus (`-`) sign ([projections.py:L45-L50](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L45-L50)).

```python
projections = {
    "public": ["-password", "-email"],  # projects all facets except password and email
}
```

During configuration, the registry parses the fields:
- Facets prefixed with a `"-"` are stripped of the prefix and added to an `excludes` list ([projections.py:L93-L94](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L93-L94)).
- Other facets are added to an `includes` list ([projections.py:L95-L96](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L95-L96)).
- If only exclusions are defined (`excludes and not includes`), the projection resolves to all available non-write-only facets minus the excluded ones ([projections.py:L98-L100](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L98-L100)).
- If includes are specified (even if exclusion strings are in the raw list), the registry resolves the projection strictly to the `includes` list, ignoring the exclusions ([projections.py:L101-L102](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L101-L102)).
- If the parsed fields list is empty, it defaults to all facets ([projections.py:L103-L104](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L103-L104)).

---

### 5. Default Projection: `Spec.default_projection`

You can specify a default projection to use when no projection is explicitly requested.

- Set the `default_projection` attribute on the inner `Spec` class ([projections.py:L39](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L39)).
- If `Spec.default_projection` is not defined (or resolves to `None`), the registry defaults to the first projection defined in the `projections` dictionary ([projections.py:L109](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L109)).
- If no projections are defined at all, the registry automatically configures a default `"__all__"` projection ([projections.py:L76-L80](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L76-L80)).

---

### 6. ProjectionRegistry API

The `[ProjectionRegistry](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L26-L146)` class manages named projections for a [Blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L826-L2075) class ([projections.py:L26-L28](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L26-L28)).

#### Methods

##### `configure()`
Configures named projections from `Spec` definitions ([projections.py:L58-L109](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L58-L109)).

```python
def configure(
    self,
    projections: dict[str, str | list[str]] | None,
    default: str | None,
    all_facet_names: set[str],
    write_only_names: set[str],
) -> None
```

- **Arguments**:
  - `projections`: Mapping of name to field list (or `"__all__"` / `"__minimal__"`).
  - `default`: Name of the default projection.
  - `all_facet_names`: Complete set of facet names.
  - `write_only_names`: Set of write-only facet names.
- **Behavior**: Excludes write-only fields from the total facets list ([projections.py:L74](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L74)) and initializes each projection name to a frozen set of facet names ([projections.py:L82-L107](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L82-L107)).

##### `resolve()`
Resolves a projection name to a frozen set of facet names ([projections.py:L111-L132](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L111-L132)).

```python
def resolve(self, name: str | None = None) -> frozenset[str]
```

- **Arguments**:
  - `name`: Projection name (defaults to `None`).
- **Returns**: A frozen set of facet names in the projection.
- **Behavior**: If `name` is `None`, resolves using the default projection name ([projections.py:L124-L125](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L124-L125)). If no default name is set, returns the set of all non-write-only facets ([projections.py:L126-L127](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L126-L127)).
- **Raises**: `[ProjectionFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L117-L126)` if the requested projection name does not exist in the registry ([projections.py:L129-L130](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L129-L130)).

#### Properties & Operators

- **`default_name`**: Returns the name of the default projection (`str | None`) ([projections.py:L134-L136](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L134-L136)).
- **`available`**: Returns a list of all registered projection names ([projections.py:L138-L140](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L138-L140)).
- **`__contains__`**: Allows checking if a projection is registered using the `in` operator (e.g., `"summary" in registry`) ([projections.py:L142-L143](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L142-L143)).

---

### 7. ProjectionFault

The `[ProjectionFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L117-L126)` exception is raised when resolving a projection name that is not registered ([projections.py:L129-L130](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/projections.py#L129-L130)).

- Defined in `aquilia/blueprints/exceptions.py` ([exceptions.py:L117-L126](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L117-L126)).
- Inherits from `[BlueprintFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L25-L56)`.
- It accepts the requested projection name and the list of available projection names ([exceptions.py:L122](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L122)).

---

### 8. Using Projections at Route Level

Selecting projections at the route/API boundary is done by subscripting the [Blueprint](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L826-L2075) class.

- Subscripting the class directly (e.g., `UserBlueprint["summary"]`) invokes `[BlueprintMeta.__getitem__](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L609-L624)`.
- This returns a `[_ProjectedRef](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L187-L201)` object ([lenses.py:L187-L201](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/lenses.py#L187-L201)), which binds the blueprint class to the requested projection string.
- This projected reference is used by controllers or serializers to shape the JSON output format dynamically.
- To access values from an instantiated blueprint instance, subscripting it (e.g., `blueprint_instance["field_name"]`) invokes `[Blueprint.__getitem__](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/core.py#L922-L924)`.

---

### 9. Code Examples

#### Standard Declaration and Selection
Here is how to define multiple named projections and select one at the route boundary:

```python
from aquilia.blueprints import Blueprint

class UserBlueprint(Blueprint):
    class Spec:
        model = User
        projections = {
            "summary": ["id", "username", "display_name"],
            "detail": ["id", "username", "display_name", "bio", "created_at"],
            "admin": "__all__",
            "minimal": "__minimal__",
        }
        default_projection = "summary"

# Route handler usage returning a projected reference:
@router.get("/users/{user_id}")
def get_user(user_id: int):
    user = db.get_user(user_id)
    # shape output with "detail" projection instead of the default "summary"
    return UserBlueprint["detail"](user)
```

#### Exclusion Projection
Define a public projection that automatically includes all facets except sensitive ones:

```python
class SensitiveUserBlueprint(Blueprint):
    class Spec:
        model = User
        projections = {
            "public": ["-password_hash", "-email_verification_token"],
        }
```
