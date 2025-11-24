from __future__ import annotations

from collections import defaultdict
from functools import reduce
from typing import Dict, Iterable, Iterator, List, Tuple

from .models import Transaction


# --------- Stream filters --------- #

def valid_transactions(records: Iterable[Transaction]) -> Iterator[Transaction]:
    return (
        t
        for t in records
        if not t.is_cancellation and t.quantity > 0 and t.unit_price > 0
    )


# --------- Aggregations --------- #

def total_revenue(records: Iterable[Transaction]) -> float:
    """
    Total revenue across all valid line items.
    Uses a generator expression to stay streamed.
    """
    return round(sum(t.line_total for t in records), 2)


def revenue_by_country(records: Iterable[Transaction]) -> Dict[str, float]:
    """
    Aggregate revenue per country.
    """
    totals: Dict[str, float] = defaultdict(float)
    for t in records:
        totals[t.country] += t.line_total
    return {country: round(amount, 2) for country, amount in totals.items()}


def monthly_revenue(records: Iterable[Transaction]) -> Dict[str, float]:
    """
    Aggregate revenue per calendar month (YYYY-MM).
    """
    totals: Dict[str, float] = defaultdict(float)
    for t in records:
        key = f"{t.invoice_date.year}-{t.invoice_date.month:02d}"
        totals[key] += t.line_total
    return {month: round(amount, 2) for month, amount in totals.items()}


def top_n_products_by_revenue(
    records: Iterable[Transaction],
    n: int = 10,
) -> List[Tuple[str, float]]:
    """
    Top N products by revenue, using Description as the product name.
    """
    per_product: Dict[str, float] = defaultdict(float)
    for t in records:
        key = t.description or t.stock_code
        per_product[key] += t.line_total

    sorted_items = sorted(
        per_product.items(),
        key=lambda item: item[1],  # lambda for sort key
        reverse=True,
    )
    return [(name, round(amount, 2)) for name, amount in sorted_items[:n]]


def top_n_customers_by_revenue(
    records: Iterable[Transaction],
    n: int = 10,
) -> List[Tuple[str, float]]:
    """
    Top N customers by revenue.
    Rows with missing CustomerID are ignored.
    """
    totals: Dict[str, float] = defaultdict(float)
    for t in records:
        if t.customer_id is None:
            continue
        totals[t.customer_id] += t.line_total

    sorted_items = sorted(
        totals.items(),
        key=lambda item: item[1],
        reverse=True,
    )
    return [(cust, round(amount, 2)) for cust, amount in sorted_items[:n]]


def avg_order_value(records: Iterable[Transaction]) -> float:
    """
    Average revenue per invoice (InvoiceNo).

    Uses functional style: reduce + small inner function instead
    of mutating a dict in-place.
    """

    def reducer(acc: Dict[str, float], t: Transaction) -> Dict[str, float]:
        total = acc.get(t.invoice_no, 0.0) + t.line_total
        return acc | {t.invoice_no: total}

    invoice_totals: Dict[str, float] = reduce(
        reducer,
        records,
        {},
    )

    if not invoice_totals:
        return 0.0

    return round(sum(invoice_totals.values()) / len(invoice_totals), 2)


def units_sold_per_product(records: Iterable[Transaction]) -> Dict[str, int]:
    """
    Units sold per product (by Description; falls back to StockCode).
    """
    counts: Dict[str, int] = defaultdict(int)
    for t in records:
        key =  t.stock_code or t.description
        counts[key] += t.quantity
    return dict(counts)


def cancellation_rate(records: Iterable[Transaction]) -> float:
    """
    Percentage of cancelled revenue over total gross revenue.

    This function demonstrates that we can also look at the
    *raw* records (including cancellations) when needed.
    """
    total = 0.0
    cancelled = 0.0

    for t in records:
        total += abs(t.line_total)
        if t.is_cancellation:
            cancelled += abs(t.line_total)

    if total == 0:
        return 0.0
    return round(100.0 * cancelled / total, 2)