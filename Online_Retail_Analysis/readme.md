# Online Retail Sales Analysis (UCI) – Functional & Stream-Based Python

This project is a small, production-style analytics tool built in Python to demonstrate:

- Functional programming  
- Stream operations  
- Data aggregation  
- Lambda expressions  

It analyzes the **Online Retail** dataset from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/352/online+retail) and turns raw transactional data into business insights for an online retailer (e.g., revenue by country, monthly trends, top products and customers, cancellation rate, etc.).

---

## 1. Problem Statement

The UCI **Online Retail** dataset contains over 540,000 transaction line items from a UK-based non-store online retailer. In its raw form (CSV/Excel), the data is not directly useful for decision-making. Typical stakeholders want to answer questions like:

- Which **countries** and **products** generate the most revenue?  
- Who are our **top customers**?  
- How does **revenue change over time**?  
- What is our **cancellation/refund rate**?  
- What is the **average order value**?

The goal of this project is to build a **Python command-line application** that:

1. **Streams** the CSV file using generator-based I/O (no heavy frameworks).  
2. Uses **functional-style transformations** (map/filter/reduce-like patterns, lambdas, pure functions).  
3. Performs **aggregation and grouping** across multiple dimensions (country, month, product, customer, invoice).  
4. Prints the **results of all analyses to the console** in a readable way.

---

## 2. Dataset Choice & How It Fits the Assignment

The assignment requires:

> “Select or construct a CSV dataset that you feel best fits the problem and document your choices and assumptions as part of your solution.”

### 2.1 Dataset Selected

I **selected** the **Online Retail** dataset from the UCI Machine Learning Repository (instead of constructing synthetic data) and exported it to a CSV file named `data/OnlineRetail.csv`.

Each row in this dataset represents a **single line item** on an invoice, with the following relevant fields:

- `InvoiceNo` – invoice identifier; values starting with `C` indicate **cancellations**.  
- `StockCode` – product code.  
- `Description` – product name.  
- `Quantity` – quantity of the product in this line.  
- `InvoiceDate` – date and time of the invoice.  
- `UnitPrice` – unit price in GBP.  
- `CustomerID` – numeric customer identifier (may be missing).  
- `Country` – customer’s country.

### 2.2 Why this dataset best fits the problem

This dataset is a good fit for the assignment for several reasons:

- **Right shape for streams & functional programming**  
  The data is at **transaction (line-item)** granularity, not pre-aggregated. That means:
  - We can **stream** a large number of rows from CSV as a generator.
  - We can apply functional-style operations (map/filter/reduce-like patterns) on raw events.
  - We must implement real aggregations: group by invoice, customer, product, country, and month.

- **Natural for the required analyses**  
  The assignment focuses on “performing data analysis on sales data.” This dataset supports:
  - Total revenue calculations  
  - Revenue by country and by month  
  - Top products and customers by revenue  
  - Average order value  
  - Cancellation / refund behavior  

- **Realistic and reproducible**  
  The dataset is public, well-documented, and widely used in teaching. This means:
  - Anyone can download the same CSV and reproduce the analysis.
  - The insights and edge cases (cancellations, missing IDs) are realistic, not artificially simplified.


### 2.3 Assumptions documented in the solution

To keep the analysis consistent and realistic, I make the following **explicit assumptions**, all of which are reflected in the code:

1. **What counts as a “valid” transaction?**  
   For core KPIs (revenue, top products/customers, etc.), I only count **valid sales**. A transaction is considered **invalid** for these metrics if:
   - `InvoiceNo` starts with `"C"` (cancellation), or  
   - `Quantity <= 0`, or  
   - `UnitPrice <= 0`.  

   This filtering is implemented in `valid_transactions`.

2. **How cancellations are treated**  
   - Cancellations are not ignored; they are analyzed via a dedicated `cancellation_rate` function.  
   - `cancellation_rate` runs on the **raw stream** (including cancellations) and:
     - uses the **absolute value** of line totals,  
     - computes total “gross” revenue,  
     - and then the percentage of that revenue that is cancelled.

3. **Missing product descriptions and customer IDs**  
   - If `Description` is missing, product-level metrics **fall back to `StockCode`** as the product identifier.  
   - If `CustomerID` is missing:
     - the row still contributes to **global revenue**,  
     - but it is **excluded from customer-level metrics** (e.g., top customers).

4. **Date parsing and invalid rows**  
   - `InvoiceDate` is parsed using a small set of known timestamp formats (e.g. `"%m/%d/%Y %H:%M"` and variants).  
   - Rows with invalid dates or numeric fields are skipped.

These assumptions are both **implemented in code** and **documented here**, which directly satisfies the assignment’s requirement to document dataset choices and assumptions.

---

## 3. Project Structure

```text
online-retail-analysis/
  online_retail/
    __init__.py
    models.py         # Transaction dataclass
    io_utils.py       # Streaming CSV loader
    analysis.py       # Pure functional aggregations
    cli.py            # Command-line interface
  tests/
    test_analysis.py  # Unit tests for analysis layer
  data/
    OnlineRetail.csv  # CSV export of UCI Online Retail dataset
  requirements.txt
  README.md
```
---

## 4. How to Run the CLI Application

### 4.1 Prerequisites

- Python **3.10+**
- `data/OnlineRetail.csv` present in the `data/` folder (CSV export of the UCI Online Retail dataset).

---

### 4.2 Setup

From the project root:

```bash
git clone <your-public-github-repo-url>.git
cd ONLINE_RETAIL_ANALYSIS


pip install -r requirements.txt
```

---

### 4.3 Run the CLI

The CLI takes a single required argument: the path to the CSV file.

```bash
python -m online_retail.cli --csv data/OnlineRetail.csv
```

This will:

- Stream the CSV file into `Transaction` objects.
- Filter out invalid / cancelled rows for core metrics.
- Run all analysis functions.
- Print the results in a structured format to the console:
  - total revenue,
  - revenue by country/month,
  - top products/customers,
  - average order value,
  - units sold,
  - cancellation rate.

If your CSV is in a different location, just change the path:

```bash
python -m online_retail.cli --csv data/OnlineRetail.csv
```
or
```bash
python -m online_retail.cli --csv /path/to/your/OnlineRetail.csv
```

---

## 5. How to Run the Tests

All analysis logic is covered by unit tests under the `tests/` directory.

From the project root (with your virtual environment activated if you’re using one):

### 5.1 Run all tests with discovery

```bash
python -m unittest discover -s tests -v
```

This will:

- Discover all test modules in the `tests/` directory.
- Run them in verbose mode (`-v`), showing each individual test name and status.

---

### 5.2 What the Test Suite Covers

The test suite covers:

- **Filtering of:**
  - cancellations,
  - zero / negative quantity,
  - zero / negative price.
- **Correct behavior of:**
  - total revenue,
  - revenue by country,
  - monthly revenue,
  - top-N products and customers,
  - average order value,
  - units sold per product,
  - cancellation rate.
- **Edge cases:**
  - behavior on empty inputs for all aggregation functions.
  - fallback from `Description` → `StockCode`.
  - top-N behavior when `n` is larger than the number of available products or customers.



# Producer_Consumer-Online-Retail-Analysis
# Online_Retail_Analysis
# Online_Retail_Analysis
