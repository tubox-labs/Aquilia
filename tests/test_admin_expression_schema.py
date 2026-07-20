import json

from aquilia import models
from aquilia.admin.site import AdminSite
from aquilia.models import expression, fields
from aquilia.models.base import Model, ModelRegistry


def test_get_model_schema_with_expression_constraints():
    # Define a temporary model with expression constraint and index
    class TempModelWithExpr(Model):
        __tablename__ = "temp_expr_model"
        id = fields.UUIDField(primary_key=True)
        email = fields.EmailField()

        class Meta:
            constraints = [models.UniqueConstraint(fields=[expression.Lower("email")], name="temp_email_unique")]
            indexes = [fields.Index(fields=[expression.Lower("email")], name="temp_email_lower_idx")]

    # Create admin site and register model
    site = AdminSite()
    site.register(TempModelWithExpr)

    try:
        # Get schema
        schema = site.get_model_schema()

        # Verify JSON serializability
        serialized = json.dumps(schema)
        assert "temp_expr_model" in serialized
        assert "LOWER" in serialized
    finally:
        # Clean up registration
        if TempModelWithExpr in site._registry:
            del site._registry[TempModelWithExpr]
        if "TempModelWithExpr" in ModelRegistry._models:
            del ModelRegistry._models["TempModelWithExpr"]
