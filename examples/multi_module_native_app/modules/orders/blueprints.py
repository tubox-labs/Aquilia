from aquilia.contracts import Contract


class OrderLineContract(Contract):
    sku: str
    quantity: int

    class Spec:
        extra_fields = "reject"

    def seal_quantity(self, data):
        if data.get("quantity", 0) <= 0:
            self.reject("quantity", "Quantity must be greater than zero")


class CreateOrderContract(Contract):
    customer_email: str
    lines: list[dict]

    class Spec:
        extra_fields = "reject"
        max_many_items = 100

    def seal_customer_email(self, data):
        if "@" not in data.get("customer_email", ""):
            self.reject("customer_email", "Customer email is required")

    def seal_lines(self, data):
        lines = data.get("lines") or []
        if not lines:
            self.reject("lines", "At least one line item is required")
        for line in lines:
            line_contract = OrderLineContract(data=line)
            if not line_contract.is_sealed():
                self.reject("lines", line_contract.errors)
