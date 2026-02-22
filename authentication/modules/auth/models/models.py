from aquilia.models import Model, fields

class UsersModel(Model):
    table = "users"

    id = fields.AutoField(primary_key=True)
    username = fields.CharField(max_length=225, default="unknown", null=False, blank=False)
    
    name = fields.CompositeField(
        schema={
            "first_name": fields.CharField(max_length=225, null=False, blank=False),
            "last_name": fields.CharField(max_length=225, null=False, blank=False)
        }, 
        prefix="name"
    )
    
    email = fields.EmailField(max_length=225, unique=True, null=False, blank=False)
    password = fields.CharField(max_length=225, null=False, blank=False)
    active = fields.BooleanField(default=False, null=False)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            fields.Index(fields=["email"])
        ]

    def __str__(self):
        return f"{self.name.get('first_name')} {self.name.get('last_name')}"
