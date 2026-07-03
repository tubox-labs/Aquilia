---
title: "Exception Filters"
description: "Handling exceptions with filters"
icon: lucide/shield-alert
---## Purpose

Exception filters intercept unhandled exceptions from controller handlers and convert them into proper HTTP responses. This provides a centralized, declarative way to handle errors across your controller methods without repetitive try-catch blocks.

Exception filters are useful for:
- Converting domain exceptions (e.g., `KeyError`, `ValueError`) into appropriate HTTP error responses
- Standardizing error response formats across your API
- Adding context-aware error handling (logging, monitoring, custom headers)
- Separating error handling logic from business logic

## ExceptionFilter API

The `ExceptionFilter` base class defines the contract for exception filters (lines 294-327):

```python
class ExceptionFilter:
    catches: list[type] = []  # Exception types this filter handles

    async def catch(
        self,
        exception: Exception,
        ctx: "RequestCtx",
    ) -> Optional["Response"]:
        """
        Handle the exception and return a Response.
        
        Return ``None`` to let the exception propagate.
        """
        raise NotImplementedError
```

### `catches` Attribute

A class-level list of exception types that this filter will handle. When an exception is raised from a controller handler, Aquilia checks each registered filter's `catches` list to find a matching handler.

### `catch` Method Signature

```python
async def catch(self, exception: Exception, ctx: RequestCtx) -> Optional[Response]
```

- **`exception`**: The exception instance that was raised
- **`ctx`**: The current request context, providing access to request data, identity, session, etc.
- **Returns**: A `Response` object to send to the client, or `None` to let the exception propagate further

## Registration

Exception filters are registered at the controller class level using the `exception_filters` attribute (line 437):

```python
class UsersController(Controller):
    prefix = "/users"
    exception_filters = [NotFoundFilter(), ValidationFilter()]
```

The `exception_filters` list is automatically copied for each controller class by the `_ControllerMeta` metaclass (lines 427-440), preventing list mutation from affecting parent classes.

## Working Example

Here's a practical example of a custom 404 filter that catches lookup errors:

```python
from aquilia.controller import Controller, ExceptionFilter
from aquilia.response import Response

class NotFoundFilter(ExceptionFilter):
    """Convert KeyError and LookupError into 404 responses."""
    
    catches = [KeyError, LookupError]

    async def catch(self, exception, ctx):
        return Response.json(
            {
                "error": "Not found",
                "detail": str(exception),
                "path": ctx.path,
                "request_id": ctx.request_id,
            },
            status=404,
        )


class ValidationFilter(ExceptionFilter):
    """Convert ValueError into 400 Bad Request responses."""
    
    catches = [ValueError]

    async def catch(self, exception, ctx):
        return Response.json(
            {
                "error": "Validation failed",
                "detail": str(exception),
            },
            status=400,
        )


class UsersController(Controller):
    prefix = "/users"
    exception_filters = [NotFoundFilter(), ValidationFilter()]

    def __init__(self, repo: UserRepository):
        self.repo = repo

    @GET("/{user_id}")
    async def get_user(self, ctx, user_id: int):
        # If user doesn't exist, repo raises KeyError
        # NotFoundFilter catches it and returns 404 JSON response
        user = self.repo.get_by_id(user_id)
        return {"user": user}

    @POST("/")
    async def create_user(self, ctx):
        data = await ctx.json()
        # If data is invalid, validation raises ValueError
        # ValidationFilter catches it and returns 400 JSON response
        user = self.repo.create(data)
        return {"user": user}
```

## Execution Order

Exception filters are evaluated in the order they appear in the `exception_filters` list. When an exception is raised:

1. Aquilia iterates through the registered filters in order
2. For each filter, it checks if the exception type is in the filter's `catches` list
3. The first matching filter's `catch()` method is invoked
4. If `catch()` returns a `Response`, that response is sent to the client
5. If `catch()` returns `None`, the exception continues to the next filter
6. If no filter handles the exception, it propagates to the framework's default error handler

**Example with multiple filters:**

```python
class UsersController(Controller):
    exception_filters = [
        SpecificErrorFilter(),      # Checked first
        GenericDatabaseFilter(),    # Checked second
        FallbackFilter(),           # Checked last
    ]
```

Best practices:
- Place more specific filters before generic ones
- Return `None` from `catch()` if you want to delegate to the next filter
- Use separate filters for different error categories (validation, not found, auth, etc.)
- Include request context in error responses for debugging (`request_id`, `path`)
