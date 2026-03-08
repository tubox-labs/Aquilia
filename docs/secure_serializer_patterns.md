# Aquilia Blueprint — Secure Serializer Patterns

**Module:** `aquilia/blueprints/`  
**Focus:** Security best practices for serializer/deserializer design  

---

## 1. Secure Deserialization Principles

### 1.1 The Trust Boundary Rule

> **All data crossing a trust boundary MUST be treated as untrusted
> until explicitly validated by the Blueprint pipeline.**

```
UNTRUSTED: HTTP body, query params, form data, headers
UNTRUSTED: Direct Blueprint(data=...) with user-supplied data
TRUSTED: Blueprint.validated_data after is_sealed() returns True
TRUSTED: Model instances from database queries
```

### 1.2 Defense in Depth Layers

```
Layer 1: Transport — Content-Type, Content-Length checks
Layer 2: Parsing — Body size limit, JSON depth limit
Layer 3: Schema — Unknown field rejection, type checking
Layer 4: Cast — Type coercion with safe conversions only
Layer 5: Seal — Constraint validation (range, pattern, length)
Layer 6: Cross-field — Business rule validation
Layer 7: Imprint — Write-back filtering (only model fields)
```

---

## 2. Secure Pattern Catalog

### 2.1 Pattern: Explicit Field Allowlist

```python
# SECURE: Only listed fields are accepted
class UserBlueprint(Blueprint):
    class Spec:
        model = User
        fields = ["name", "email", "bio"]  # Explicit allowlist
        extra_fields = "reject"  # Reject unknown fields

# INSECURE: All model fields exposed
class UserBlueprint(Blueprint):
    class Spec:
        model = User
        fields = "__all__"  # Dangerous — includes internal fields
```

### 2.2 Pattern: Separate Input/Output Blueprints

```python
class UserCreateInput(Blueprint):
    """Input-only Blueprint for user creation."""
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$")
    password: str = Field(write_only=True, min_length=8)

    class Spec:
        model = User
        extra_fields = "reject"

class UserOutput(Blueprint):
    """Output-only Blueprint for user responses."""
    id: int
    name: str
    email: str
    created_at: datetime = Field(read_only=True)
    
    class Spec:
        model = User
        projections = {
            "public": ["id", "name"],
            "self": ["id", "name", "email", "created_at"],
        }
```

### 2.3 Pattern: Role-Based Projections

```python
class OrderBlueprint(Blueprint):
    class Spec:
        model = Order
        projections = {
            "customer": ["id", "status", "total", "items"],
            "support": ["id", "status", "total", "items", "customer_id", "notes"],
            "admin": "__all__",
        }

# In controller:
@get("/orders/{id}")
async def get_order(self, id: int, ctx):
    order = await Order.objects.get(id=id)
    projection = "admin" if ctx.identity.is_admin else "customer"
    bp = OrderBlueprint(instance=order, projection=projection)
    return bp.data
```

### 2.4 Pattern: Immutable Computed Fields

```python
class InvoiceBlueprint(Blueprint):
    items: list[ItemBlueprint]
    
    # Computed — cannot be overridden by input
    subtotal = Computed(lambda inv: sum(i.price * i.qty for i in inv.items))
    tax = Computed(lambda inv: inv.subtotal * inv.tax_rate)
    total = Computed(lambda inv: inv.subtotal + inv.tax)
```

### 2.5 Pattern: Audit Trail via Hidden + Inject

```python
class ArticleBlueprint(Blueprint):
    title: str
    body: str
    
    # Automatically injected from DI — cannot be user-supplied
    created_by = Inject(token="current_user_id")
    ip_address = Inject(via="request.client.host")
    
    class Spec:
        model = Article
```

### 2.6 Pattern: Safe Partial Updates

```python
@patch("/users/{id}")
async def update_user(self, id: int, user: UserUpdateBlueprint):
    existing = await User.objects.get(id=id)
    # partial=True: only update provided fields
    bp = UserUpdateBlueprint(data=user.validated_data, partial=True)
    if bp.is_sealed():
        await bp.imprint(existing)
```

### 2.7 Pattern: Cross-Field Security Validation

```python
class TransferBlueprint(Blueprint):
    from_account: int
    to_account: int
    amount: Decimal = Field(ge=Decimal("0.01"), le=Decimal("1000000"))
    
    def seal_accounts_different(self, data):
        if data["from_account"] == data["to_account"]:
            self.reject("to_account", "Cannot transfer to same account")
    
    async def async_seal_sufficient_funds(self, data):
        account = await Account.objects.get(id=data["from_account"])
        if account.balance < data["amount"]:
            self.reject("amount", "Insufficient funds")
    
    async def async_seal_account_ownership(self, data):
        user_id = self.context.get("user_id")
        account = await Account.objects.get(id=data["from_account"])
        if account.owner_id != user_id:
            self.reject("from_account", "Not your account")
```

---

## 3. Anti-Patterns to Avoid

### 3.1 Trusting validated_data Without Sealing

```python
# DANGEROUS: Using data before sealing
bp = UserBlueprint(data=request_data)
await bp.imprint()  # Raises ImprintFault, but easy to miss

# CORRECT: Always seal first
bp = UserBlueprint(data=request_data)
if not bp.is_sealed():
    return ErrorResponse(bp.errors)
await bp.imprint()
```

### 3.2 Exposing Internal Fields

```python
# DANGEROUS: Exposes password_hash, is_superuser, etc.
class UserBlueprint(Blueprint):
    class Spec:
        model = User
        fields = "__all__"

# SAFE: Explicit field list
class UserBlueprint(Blueprint):
    class Spec:
        model = User
        fields = ["id", "name", "email", "avatar"]
```

### 3.3 Missing Write-Only on Passwords

```python
# DANGEROUS: Password appears in API responses
password: str = Field(min_length=8)

# SAFE: Never in output
password: str = Field(write_only=True, min_length=8)
```

### 3.4 Dynamic Blueprint from User Input

```python
# EXTREMELY DANGEROUS: Never create Blueprints from user input
fields = request.json()["schema"]["fields"]
DynamicBP = type("DynamicBP", (Blueprint,), {
    "__annotations__": {f["name"]: str for f in fields}
})
```

---

## 4. Security Checklist

- [ ] All input Blueprints have explicit field lists (not `"__all__"`)
- [ ] Sensitive fields marked `write_only=True`
- [ ] Internal/computed fields marked `read_only=True`
- [ ] `extra_fields = "reject"` in Spec for input Blueprints
- [ ] Passwords never appear in output projections
- [ ] Role-based projections for multi-audience APIs
- [ ] Cross-field seals for business rule validation
- [ ] Async seals for authorization/ownership checks
- [ ] No dynamic Blueprint creation from user input
- [ ] Always call `is_sealed()` before `imprint()`

---

*End of Secure Serializer Patterns — Phase 10*
