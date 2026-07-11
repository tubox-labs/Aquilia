from aquilia.contracts import Contract


class ProjectCreateContract(Contract):
    key: str
    name: str
    summary: str | None = None
    owner_email: str
    status: str = "planned"

    class Spec:
        extra_fields = "reject"

    def seal_key(self, data):
        key = data.get("key", "").strip().upper()
        if not key:
            self.reject("key", "Project key is required")
        data["key"] = key

    def seal_owner_email(self, data):
        email = data.get("owner_email", "")
        if "@" not in email:
            self.reject("owner_email", "Owner email must look like an email address")


class ProjectUpdateContract(Contract):
    name: str | None = None
    summary: str | None = None
    owner_email: str | None = None
    status: str | None = None
    archived: bool | None = None

    class Spec:
        extra_fields = "reject"
