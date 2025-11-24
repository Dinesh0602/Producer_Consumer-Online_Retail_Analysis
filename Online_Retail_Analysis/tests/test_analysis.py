import unittest
from datetime import datetime

from online_retail.models import Transaction
from online_retail.analysis import (
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


class AnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        # Small handcrafted sample resembling UCI Online Retail rows
        self.raw = [
            Transaction(
                invoice_no="536365",
                stock_code="85123A",
                description="WHITE HANGING HEART T-LIGHT HOLDER",
                quantity=6,
                invoice_date=datetime(2010, 12, 1, 8, 26),
                unit_price=2.55,
                customer_id="17850",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="536365",
                stock_code="71053",
                description="WHITE METAL LANTERN",
                quantity=6,
                invoice_date=datetime(2010, 12, 1, 8, 26),
                unit_price=3.39,
                customer_id="17850",
                country="United Kingdom",
            ),
            # Cancellation row – should be filtered out by valid_transactions
            Transaction(
                invoice_no="C536379",
                stock_code="85123A",
                description="WHITE HANGING HEART T-LIGHT HOLDER",
                quantity=-6,
                invoice_date=datetime(2010, 12, 1, 9, 41),
                unit_price=2.55,
                customer_id="17850",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="536370",
                stock_code="84029G",
                description="KNITTED UNION FLAG HOT WATER BOTTLE",
                quantity=2,
                invoice_date=datetime(2010, 12, 1, 9, 0),
                unit_price=3.39,
                customer_id="13047",
                country="France",
            ),
        ]

        # Apply same filter as CLI
        self.records = list(valid_transactions(self.raw))


    # -------- valid_transactions -------- #
    def test_valid_transactions_filters_cancellations(self) -> None:
        # We started with 4 rows, 1 is a cancellation
        self.assertEqual(len(self.records), 3)
        self.assertTrue(all(not t.is_cancellation for t in self.records))
        self.assertTrue(all(t.quantity > 0 and t.unit_price > 0 for t in self.records))

    def test_valid_transactions_all_cancellations(self) -> None:
        cancelled_only = [
            Transaction(
                invoice_no="C100",
                stock_code="X1",
                description="Cancelled item",
                quantity=-1,
                invoice_date=datetime(2011, 1, 1, 9, 0),
                unit_price=10.0,
                customer_id="11111",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="C101",
                stock_code="X2",
                description="Cancelled item 2",
                quantity=-2,
                invoice_date=datetime(2011, 1, 1, 9, 5),
                unit_price=5.0,
                customer_id="22222",
                country="United Kingdom",
            ),
        ]
        filtered = list(valid_transactions(cancelled_only))
        # All should be filtered out
        self.assertEqual(filtered, [])
        self.assertEqual(len(filtered), 0)


    def test_valid_transactions_filters_zero_quantity_and_price(self) -> None:
        zero_cases = [
            Transaction(
                invoice_no="100000",
                stock_code="ZQ0",
                description="Zero quantity",
                quantity=0,  # invalid
                invoice_date=datetime(2011, 1, 1, 10, 0),
                unit_price=10.0,
                customer_id="90000",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="100001",
                stock_code="ZP0",
                description="Zero price",
                quantity=5,
                invoice_date=datetime(2011, 1, 1, 10, 5),
                unit_price=0.0,  # invalid
                customer_id="90001",
                country="United Kingdom",
            ),
        ]
        filtered = list(valid_transactions(zero_cases))
        # Both should be filtered out
        self.assertEqual(filtered, [])
        self.assertEqual(len(filtered), 0)


    # -------- total_revenue -------- #
    def test_total_revenue(self) -> None:
        # 1st: 6 * 2.55 = 15.30
        # 2nd: 6 * 3.39 = 20.34
        # Sum = 15.30 + 20.34 + 6.78 = 42.42
        self.assertEqual(total_revenue(self.records), 42.42)

    def test_total_revenue_empty(self) -> None:
        self.assertEqual(total_revenue([]), 0.0)

    # -------- revenue_by_country -------- #
    def test_revenue_by_country(self) -> None:
        result = revenue_by_country(self.records)
        # UK: first two lines
        self.assertAlmostEqual(result["United Kingdom"], 35.64)
        # France: last line
        self.assertAlmostEqual(result["France"], 6.78)

    def test_revenue_by_country_empty(self) -> None:
        self.assertEqual(revenue_by_country([]), {})


    # -------- monthly_revenue -------- #
    def test_monthly_revenue(self) -> None:
        result = monthly_revenue(self.records)
        # All sample rows fall in December 2010
        self.assertAlmostEqual(result["2010-12"], 42.42)

    def test_monthly_revenue_empty(self) -> None:
        self.assertEqual(monthly_revenue([]), {})


    # -------- top_n_products_by_revenue -------- #
    def test_top_n_products_by_revenue(self) -> None:
        result = top_n_products_by_revenue(self.records, n=2)
        names = [name for name, _ in result]
        self.assertIn("WHITE METAL LANTERN", names)
        self.assertIn("WHITE HANGING HEART T-LIGHT HOLDER", names)


    def test_top_n_products_with_less_than_n_items(self) -> None:
        # Only 3 valid records, but ask for top 10
        result = top_n_products_by_revenue(self.records, n=10)
        # Should not crash and should just return 3 items
        self.assertEqual(len(result), 3)


    # -------- top_n_customers_by_revenue -------- #
    def test_top_n_customers_by_revenue(self) -> None:
        result = top_n_customers_by_revenue(self.records, n=2)
        # Customer 17850 spent 35.64, 13047 spent 6.78
        self.assertEqual(result[0][0], "17850")
        self.assertEqual(len(result), 2)


    def test_top_n_customers_with_less_than_n_customers(self) -> None:
        # We have only 2 distinct customers
        result = top_n_customers_by_revenue(self.records, n=10)
        self.assertEqual(len(result), 2)


    # -------- avg_order_value -------- #
    def test_avg_order_value(self) -> None:
        # Two invoices after filter:
        # 536365: 15.30 + 20.34 = 35.64
        # 536370: 6.78
        # Avg = (35.64 + 6.78) / 2 = 21.21
        self.assertAlmostEqual(avg_order_value(self.records), 21.21)

    def test_avg_order_value_empty(self) -> None:
        self.assertEqual(avg_order_value([]), 0.0)


    # -------- units_sold_per_product -------- #
    def test_units_sold_per_product(self) -> None:
        result = units_sold_per_product(self.records)
        self.assertEqual(result["85123A"], 6)
        self.assertEqual(result["71053"], 6)
        self.assertEqual(
            result["84029G"],
            2,
        )

    def test_units_sold_per_product_fallback_to_stock_code(self) -> None:
        anonymous = Transaction(
            invoice_no="999999",
            stock_code="ABC123",
            description=None,  # no description
            quantity=3,
            invoice_date=datetime(2011, 1, 1, 10, 0),
            unit_price=1.0,
            customer_id="99999",
            country="Testland",
        )
        result = units_sold_per_product([anonymous])
        # Should use stock_code as key when description is None
        self.assertIn("ABC123", result)
        self.assertEqual(result["ABC123"], 3)
        self.assertEqual(len(result), 1)


    # -------- cancellation_rate -------- #
    def test_cancellation_rate(self) -> None:
        # In self.raw:
        #   valid lines total = 42.42
        #   cancelled line value = -6 * 2.55 = -15.30 (absolute 15.30)
        # Gross = 42.42 + 15.30 = 57.72
        # cancellation rate ≈ 15.30 / 57.72 * 100 ≈ 26.5%
        self.assertAlmostEqual(cancellation_rate(self.raw), 26.5, places=1)

    def test_cancellation_rate_no_data(self) -> None:
        self.assertEqual(cancellation_rate([]), 0.0)

    def test_cancellation_rate_all_cancellations(self) -> None:
        cancelled_only = [
            Transaction(
                invoice_no="C200",
                stock_code="Y1",
                description="Cancelled item A",
                quantity=-3,
                invoice_date=datetime(2011, 2, 1, 9, 0),
                unit_price=2.0,
                customer_id="11111",
                country="United Kingdom",
            ),
            Transaction(
                invoice_no="C201",
                stock_code="Y2",
                description="Cancelled item B",
                quantity=-2,
                invoice_date=datetime(2011, 2, 1, 9, 5),
                unit_price=3.0,
                customer_id="22222",
                country="United Kingdom",
            ),
        ]
        # All revenue is cancelled => cancellation_rate should be 100%
        self.assertEqual(cancellation_rate(cancelled_only), 100.0)


if __name__ == "__main__":
    unittest.main()