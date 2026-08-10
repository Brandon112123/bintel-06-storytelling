"""storytelling_custom_smith.py - custom BI storytelling project.

Business Question:
How concentrated are total sales among customers, and how many customers
generate 80% of company revenue?

Author: Brandon Smith

Run from the project root:
uv run python -m bizintel.storytelling_custom_smith
"""

from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bizintel.utils_logger import LOG, log_header

DATA_FILE: Final[Path] = Path("data/reporting/sales_reporting_case.csv")
OUTPUT_DIR: Final[Path] = Path("docs/images")
TOP_CUSTOMERS_CHART: Final[Path] = OUTPUT_DIR / "top_customers_sales_smith.png"
PARETO_CHART: Final[Path] = OUTPUT_DIR / "customer_revenue_pareto_smith.png"
TARGET_SHARE: Final[float] = 0.80


def load_data(file_path: Path) -> pd.DataFrame:
    """Load and validate the reporting-ready sales data."""
    LOG.info("Loading reporting-ready sales data")
    df = pd.read_csv(file_path)

    required = {"TransactionID", "CustomerID", "CustomerName", "SaleAmount"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df["SaleAmount"] = pd.to_numeric(df["SaleAmount"], errors="coerce")
    if df["SaleAmount"].isna().any():
        raise ValueError("SaleAmount contains invalid values.")

    LOG.info(f"  Loaded {len(df)} sales transactions")
    return df


def summarize_customer_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate total sales and transaction count for each customer."""
    summary = (
        df.groupby(["CustomerID", "CustomerName"], as_index=False)
        .agg(
            TotalSales=("SaleAmount", "sum"),
            Transactions=("TransactionID", "count"),
        )
        .sort_values("TotalSales", ascending=False)
        .reset_index(drop=True)
    )

    summary["TotalSales"] = summary["TotalSales"].round(2)
    total_sales = summary["TotalSales"].sum()
    summary["CumulativeSales"] = summary["TotalSales"].cumsum()
    summary["CumulativeShare"] = summary["CumulativeSales"] / total_sales

    LOG.info(f"  Customers summarized: {len(summary)}")
    return summary


def customers_for_target(summary: pd.DataFrame, target: float) -> int:
    """Return the number of top customers needed to reach a revenue target."""
    return int((summary["CumulativeShare"] < target).sum() + 1)


def plot_top_customers(summary: pd.DataFrame) -> None:
    """Create a polished 3D column chart for the top ten customers."""
    top10 = summary.head(10).reset_index(drop=True)

    fig = plt.figure(figsize=(13, 8))
    ax = fig.add_subplot(111, projection="3d")

    x = np.arange(len(top10))
    y = np.zeros(len(top10))
    z = np.zeros(len(top10))
    dx = np.full(len(top10), 0.62)
    dy = np.full(len(top10), 0.72)
    dz = top10["TotalSales"].to_numpy()

    ax.bar3d(x, y, z, dx, dy, dz, shade=True)

    for i, value in enumerate(dz):
        ax.text(
            i + 0.31,
            0.36,
            value + (dz.max() * 0.025),
            f"${value / 1000:.1f}K",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    short_names = [
        name if len(name) <= 14 else name[:12] + "…" for name in top10["CustomerName"]
    ]

    ax.set_title("Top 10 Customers by Total Sales", pad=20)
    ax.set_xlabel("Customer")
    ax.set_zlabel("Total Sales ($)", labelpad=10)
    ax.set_xticks(x + 0.31)
    ax.set_xticklabels(short_names, rotation=35, ha="right")
    ax.set_yticks([])
    ax.view_init(elev=24, azim=-58)
    ax.set_box_aspect((2.5, 0.7, 1.2))

    plt.tight_layout()
    plt.savefig(TOP_CUSTOMERS_CHART, dpi=180, bbox_inches="tight")
    LOG.info(f"Saved 3D customer sales chart: {TOP_CUSTOMERS_CHART}")


def plot_pareto(summary: pd.DataFrame, target_count: int) -> None:
    """Create a cumulative revenue-share chart."""
    x = range(1, len(summary) + 1)
    plt.figure(figsize=(10, 6))
    plt.plot(x, summary["CumulativeShare"] * 100)
    plt.axhline(TARGET_SHARE * 100, linestyle="--")
    plt.axvline(target_count, linestyle="--")
    plt.title("Customer Concentration: Cumulative Share of Sales")
    plt.xlabel("Customers Ranked by Total Sales")
    plt.ylabel("Cumulative Share of Sales (%)")
    plt.tight_layout()
    plt.savefig(PARETO_CHART, bbox_inches="tight")
    LOG.info(f"Saved chart: {PARETO_CHART}")


def main() -> None:
    """Run the custom customer concentration storytelling analysis."""
    log_header(LOG, "BI")
    LOG.info("START custom customer concentration analysis")

    df = load_data(DATA_FILE)
    summary = summarize_customer_sales(df)
    target_count = customers_for_target(summary, TARGET_SHARE)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_top_customers(summary)
    plot_pareto(summary, target_count)

    total_customers = len(summary)
    top_customer = summary.iloc[0]
    target_percent = (target_count / total_customers) * 100

    LOG.info("Identifying key results")
    LOG.info(f"  Total customers: {total_customers}")
    LOG.info(f"  Top customer: {top_customer['CustomerName']}")
    LOG.info(f"  Top customer sales: ${top_customer['TotalSales']:,.2f}")
    LOG.info(f"  Customers needed for 80% of sales: {target_count}")
    LOG.info(f"  Percent of customers needed: {target_percent:.1f}%")
    LOG.info("Custom storytelling workflow complete")
    LOG.info("Executed successfully!")

    plt.show()


if __name__ == "__main__":
    main()
