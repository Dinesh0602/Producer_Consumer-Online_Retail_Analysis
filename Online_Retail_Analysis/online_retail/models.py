from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Transaction:
    """
    Represents one line item in the Online Retail dataset.

    Fields mirror UCI schema:
    - InvoiceNo, StockCode, Description, Quantity,
      InvoiceDate, UnitPrice, CustomerID, Country
    """
    invoice_no: str
    stock_code: str
    description: Optional[str]
    quantity: int
    invoice_date: datetime
    unit_price: float
    customer_id: Optional[str]
    country: str

    @property
    def line_total(self) -> float:
        """Total value for this line item."""
        return self.quantity * self.unit_price

    @property
    def is_cancellation(self) -> bool:
        """
        UCI notes: invoice numbers starting with 'C' are cancellations.
        """
        return self.invoice_no.startswith("C")