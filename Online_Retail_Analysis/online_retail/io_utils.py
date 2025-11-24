from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from .models import Transaction


def _parse_invoice_date(raw: str) -> datetime:
    return datetime.strptime(raw.strip(), "%m/%d/%y %H:%M")



def _opt_str(val: str | None) -> Optional[str]:
    if val is None:
        return None
    v = val.strip()
    return v or None


def load_transactions(csv_path: str | Path) -> Iterator[Transaction]:
    """
    Lazily load Transaction objects from an Online Retail CSV file.

    This is a generator:
      - streams rows one by one
      - fits well with functional/stream pipelines
    """
    path = Path(csv_path)

    # Many copies of this dataset need ISO-8859-1 to read descriptions cleanly
    with path.open(newline="", encoding="ISO-8859-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                quantity = int(row["Quantity"])
                unit_price = float(row["UnitPrice"])
            except (KeyError, TypeError, ValueError):
                # Skip rows with invalid numerics
                continue

            
            try:
                invoice_date = _parse_invoice_date(row["InvoiceDate"])
            except ValueError as e:
                continue

            yield Transaction(
                invoice_no=row["InvoiceNo"].strip(),
                stock_code=row["StockCode"].strip(),
                description=_opt_str(row.get("Description")),
                quantity=quantity,
                invoice_date=invoice_date ,
                unit_price=unit_price,
                customer_id=_opt_str(row.get("CustomerID")),
                country=row["Country"].strip(),
            )