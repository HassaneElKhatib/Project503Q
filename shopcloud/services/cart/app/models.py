"""Cart API models."""
from pydantic import BaseModel, Field


class CartItem(BaseModel):
    """One product line in a cart."""

    product_id: str
    product_name: str
    unit_price_cents: int = Field(..., ge=0)
    quantity: int = Field(..., ge=1, le=99)
    currency: str = Field(default="USD")

    @property
    def line_total_cents(self) -> int:
        return self.unit_price_cents * self.quantity


class Cart(BaseModel):
    """A customer's shopping cart."""

    customer_id: str
    items: list[CartItem] = Field(default_factory=list)
    currency: str = Field(default="USD")

    @property
    def total_cents(self) -> int:
        return sum(item.line_total_cents for item in self.items)

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)


class AddItemRequest(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=50)
    quantity: int = Field(default=1, ge=1, le=99)


class UpdateQuantityRequest(BaseModel):
    quantity: int = Field(..., ge=0, le=99, description="Set to 0 to remove")
