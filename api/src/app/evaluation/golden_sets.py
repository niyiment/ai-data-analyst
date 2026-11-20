"""Built-in golden question sets for evaluation (docs/TESTING.md 9.2)."""

from app.evaluation.schemas import GoldenQuestion, GoldenSet

RETAIL_SALES_SET = GoldenSet(
    name="retail_sales",
    demo_schema="demo_retail_sales",
    description="Retail sales orders across regions, categories, and return flags.",
    questions=[
        GoldenQuestion(
            id="rs-01",
            question="How many total orders are in the dataset?",
            reference_sql="SELECT COUNT(*) AS total_orders FROM retail_sales",
            category="aggregate",
            difficulty="easy",
        ),
        GoldenQuestion(
            id="rs-02",
            question="What is the total revenue by region?",
            reference_sql=(
                "SELECT region, SUM(revenue) AS total_revenue "
                "FROM retail_sales GROUP BY region"
            ),
            category="group_by",
            difficulty="easy",
        ),
        GoldenQuestion(
            id="rs-03",
            question="Which category generated the highest total revenue?",
            reference_sql=(
                "SELECT category, SUM(revenue) AS total_revenue "
                "FROM retail_sales GROUP BY category ORDER BY total_revenue DESC LIMIT 1"
            ),
            category="ranking",
            difficulty="medium",
            order_sensitive=True,
        ),
        GoldenQuestion(
            id="rs-04",
            question="List all returned orders with their product and revenue.",
            reference_sql=(
                "SELECT order_id, product, revenue FROM retail_sales WHERE returned = TRUE"
            ),
            category="filter",
            difficulty="easy",
        ),
        GoldenQuestion(
            id="rs-05",
            question="What is the average unit price per category?",
            reference_sql=(
                "SELECT category, AVG(unit_price) AS avg_price "
                "FROM retail_sales GROUP BY category"
            ),
            category="group_by",
            difficulty="medium",
        ),
        GoldenQuestion(
            id="rs-06",
            question="What are the top 3 products by total units sold?",
            reference_sql=(
                "SELECT product, SUM(units) AS total_units "
                "FROM retail_sales GROUP BY product ORDER BY total_units DESC LIMIT 3"
            ),
            category="ranking",
            difficulty="medium",
            order_sensitive=True,
        ),
        GoldenQuestion(
            id="rs-07",
            question="What is the total revenue for orders placed in January 2026?",
            reference_sql=(
                "SELECT SUM(revenue) AS jan_revenue FROM retail_sales "
                "WHERE order_date >= '2026-01-01' AND order_date < '2026-02-01'"
            ),
            category="date_logic",
            difficulty="medium",
        ),
        GoldenQuestion(
            id="rs-08",
            question="How many orders were not returned in the North region?",
            reference_sql=(
                "SELECT COUNT(*) AS count FROM retail_sales "
                "WHERE region = 'North' AND returned = FALSE"
            ),
            category="filter",
            difficulty="medium",
        ),
    ],
)

GOLDEN_SETS: dict[str, GoldenSet] = {
    RETAIL_SALES_SET.name: RETAIL_SALES_SET,
}
