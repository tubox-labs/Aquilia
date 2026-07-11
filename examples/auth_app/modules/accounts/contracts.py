from aquilia.contracts import Contract


class RegisterContract(Contract):
    email: str
    password: str
    name: str

    class Spec:
        extra_fields = "reject"

    def seal_email(self, data):
        email = data.get("email", "").strip().lower()
        if "@" not in email:
            self.reject("email", "Email address is required")
        data["email"] = email

    def seal_password(self, data):
        if len(data.get("password", "")) < 8:
            self.reject("password", "Password must be at least 8 characters")


class LoginContract(Contract):
    email: str
    password: str

    class Spec:
        extra_fields = "reject"

    def seal_email(self, data):
        data["email"] = data.get("email", "").strip().lower()
