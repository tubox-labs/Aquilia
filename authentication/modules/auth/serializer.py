from aquilia.serializers import ModelSerializer, Serializer, fields
from .models.models import UsersModel


class NameSerializer(Serializer):
    first_name = fields.CharField(max_length = 225)
    last_name = fields.CharField(max_length = 225)


class RegisterInputModel(Serializer):
    username = fields.CharField(max_length = 225)
    email = fields.EmailField(max_length=225)
    password = fields.CharField(max_length=225)
    name = NameSerializer


class UserOutputModel(ModelSerializer):
    name = NameSerializer

    class Meta:
        model = UsersModel
        fields = ["__all__"]

        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "password": {"write_only": True}
        }
