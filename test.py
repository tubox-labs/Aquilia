from aquilia.blueprints import Blueprint, NestedBlueprintFacet

class NameBlueprint(Blueprint):
    first_name: str
    last_name: str

class Users(Blueprint):
    name: NameBlueprint


user = Users(data={
    "name": {
        "first_name": "Pawan",
        "last_name": "Kumar"
    }
})

if user.is_sealed():
    print(user.data)
else:
    print(user.errors)