from aquilia.contracts import Contract


class ProductCreateContract(Contract):
    sku: str
    name: str
    price_cents: int
    active: bool = True
    tags: list[str] = []

    class Spec:
        extra_fields = "reject"

    def seal_sku(self, data):
        sku = data.get("sku", "").strip().upper()
        if not sku:
            self.reject("sku", "SKU is required")
        data["sku"] = sku

    def seal_price_cents(self, data):
        if data.get("price_cents", 0) < 0:
            self.reject("price_cents", "Price must be zero or greater")


class ProductUpdateContract(Contract):
    name: str | None = None
    price_cents: int | None = None
    active: bool | None = None
    tags: list[str] | None = None

    class Spec:
        extra_fields = "reject"

    def seal_price_cents(self, data):
        value = data.get("price_cents")
        if value is not None and value < 0:
            self.reject("price_cents", "Price must be zero or greater")
