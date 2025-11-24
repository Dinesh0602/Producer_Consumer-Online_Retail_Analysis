from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .analysis import (
    avg_order_value,
    cancellation_rate,
    monthly_revenue,
    revenue_by_country,
    top_n_customers_by_revenue,
    top_n_products_by_revenue,
    total_revenue,
    units_sold_per_product,
    valid_transactions,
)
from .io_utils import load_transactions
from .models import Transaction


def run_analyses(records: List[Transaction]) -> None:
    print("=== Online Retail Sales Analysis (UCI) ===")

    print("\nTotal revenue (valid, non-cancelled):")
    print(f"  ${total_revenue(records):,.2f}")

    print("\nRevenue by country (top 10):")
    for country, amount in sorted(
        revenue_by_country(records).items(),
        key=lambda kv: kv[1],
        reverse=True,
    )[:10]:
        print(f"  {country:20s} ${amount:,.2f}")

    print("\nMonthly revenue (YYYY-MM):")
    for month, amount in sorted(monthly_revenue(records).items()):
        print(f"  {month}  ${amount:,.2f}")

    print("\nTop 10 products by revenue:")
    for name, amount in top_n_products_by_revenue(records, n=10):
        print(f"  {name[:40]:40s} ${amount:,.2f}")

    print("\nTop 10 customers by revenue:")
    for cust, amount in top_n_customers_by_revenue(records, n=10):
        print(f"  {cust:10s} ${amount:,.2f}")

    print("\nAverage order value (per invoice):")
    print(f"  ${avg_order_value(records):,.2f}")

    print("\nUnits sold per product (first 10):")
    for name, units in list(units_sold_per_product(records).items())[:10]:
        print(f"  {name[:40]:40s} {units} units")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Online Retail CSV analysis using functional & stream-based Python."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        required=True,
        help="Path to Online Retail CSV file (e.g., data/OnlineRetail.csv).",
    )
    args = parser.parse_args()

    raw_iter = load_transactions(args.csv)

    # Apply streaming filter and then materialize once to reuse
    valid_list: List[Transaction] = list(valid_transactions(raw_iter))
    run_analyses(valid_list)


    raw_again = load_transactions(args.csv)
    print("\nCancellation rate (percentage of cancelled revenue over gross):")
    print(f"  {cancellation_rate(raw_again):.2f}%")



if __name__ == "__main__":
    main()