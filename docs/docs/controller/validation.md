---
title: "Validation"
description: "Request validation"
icon: lucide/check-square
---Controller-layer request body validation via Aquilia Blueprints.

## validate_body() Signature

The `validate_body()` decorator parses and validates request bodies through Blueprint classes. On success, it injects the validated `body: dict` as a keyword argument to the handler. On failure, it returns HTTP 422 Unprocessable Entity with structured errors.

**Source:** Lines 47-53

```python
def validate_body(blueprint_class: type, *, projection: str = "__all__") -> Any:
    """
    Decorator: parse + validate the request body through a Blueprint.

    On success:  injects ``body: dict`` as the first extra keyword argument.
    On failure:  returns HTTP 422 Unprocessable Entity with structured errors.

    Args:
        blueprint_class: The Blueprint class to validate against.
        projection:      Blueprint projection to use for allowed fields.
    """
```

### Parameters

- **blueprint_class** (`type`): The Blueprint class to validate against
- **projection** (`str`, optional): Blueprint projection to use for allowed fields. Defaults to `"__all__"`

### Behavior

The decorator handles multiple content types (lines 58-76):

- **application/json**: Parses JSON body
- **multipart/form-data**: Parses multipart form data
- **application/x-www-form-urlencoded**: Parses URL-encoded forms
- **Fallback**: Attempts JSON parsing, then form parsing

On validation success, the handler receives `body` as a keyword argument containing the validated data (line 108).

## ValidationFault

Base fault class for all validation-related faults. Uses the custom `VALIDATION_DOMAIN` fault domain (line 22).

**Source:** Lines 25-27

```python
class ValidationFault(Fault):
    domain = VALIDATION_DOMAIN
    severity = Severity.WARN
```

- **Domain**: `FaultDomain.custom("validation", "Request body validation faults")` (line 22)
- **Severity**: `Severity.WARN`

## RequestBodyValidationFault

Raised when request body fails Blueprint validation.

**Source:** Lines 30-32

```python
class RequestBodyValidationFault(ValidationFault):
    code = "validation.body_invalid"
    message = "Request body failed Blueprint validation"
```

- **Code**: `"validation.body_invalid"`
- **Message**: `"Request body failed Blueprint validation"`
- **HTTP Status**: 422 Unprocessable Entity (line 97)

When validation fails, the response includes (lines 94-97):
- `error`: Fault message
- `code`: Fault code
- `detail`: Detailed validation errors from Blueprint

### RequestBodyParseFault

Raised when request body cannot be parsed.

**Source:** Lines 35-37

```python
class RequestBodyParseFault(ValidationFault):
    code = "validation.body_parse_error"
    message = "Request body could not be parsed"
```

- **Code**: `"validation.body_parse_error"`
- **Message**: `"Request body could not be parsed"`
- **HTTP Status**: 400 Bad Request (line 80)

## Blueprint Integration

The validator integrates with Aquilia Blueprints through the following mechanism (lines 84-107):

1. **Instantiation**: Creates a Blueprint instance with the parsed data and projection (line 84)
2. **Validation**: Calls `is_sealed_async()` if available, otherwise `is_sealed()` (lines 85-88)
3. **Error Collection**: Retrieves validation errors via `errors` attribute or `seal_errors()` method (lines 90-91)
4. **Data Extraction**: Uses `validated_data` attribute if available (line 106)

### Async Support

The decorator supports both synchronous and asynchronous Blueprint validation (lines 85-88):

```python
if hasattr(bp, "is_sealed_async"):
    is_ok = await bp.is_sealed_async()
else:
    is_ok = bp.is_sealed()
```

## Code Examples

### Basic Usage

**Source Example:** Lines 5-17 (module docstring)

```python
from aquilia import Controller, POST, RequestCtx, Response
from aquilia.controller.validation import validate_body
from myapp.users.blueprints import CreateUserBlueprint

class UsersController(Controller):
    prefix = "/users"

    @POST("/")
    @validate_body(CreateUserBlueprint)
    async def create_user(self, ctx: RequestCtx, body: dict):
        user = await self.user_service.create(**body)
        return Response.json({"id": user.id}, status=201)
```

### With Custom Projection

```python
from aquilia import Controller, PUT, RequestCtx, Response
from aquilia.controller.validation import validate_body
from myapp.users.blueprints import UserBlueprint

class UsersController(Controller):
    prefix = "/users"

    @PUT("/{user_id}")
    @validate_body(UserBlueprint, projection="update")
    async def update_user(self, ctx: RequestCtx, user_id: str, body: dict):
        user = await self.user_service.update(user_id, **body)
        return Response.json(user.to_dict())
```

### Error Response Format

When validation fails (lines 94-97), the response structure is:

```json
{
  "error": "Request body failed Blueprint validation",
  "code": "validation.body_invalid",
  "detail": {
    "email": ["Invalid email format"],
    "age": ["Must be at least 18"]
  }
}
```

When parsing fails (lines 78-81), the response structure is:

```json
{
  "error": "Request body could not be parsed",
  "code": "validation.body_parse_error"
}
```

### Content Type Handling

The decorator automatically handles different content types (lines 58-76):

```python
# JSON request
# Content-Type: application/json
# Body: {"name": "John", "email": "john@example.com"}

# Form data request
# Content-Type: application/x-www-form-urlencoded
# Body: name=John&email=john@example.com

# Multipart request
# Content-Type: multipart/form-data
# Body: (multipart form with files and fields)
```

All content types are parsed and passed to the Blueprint for validation.
