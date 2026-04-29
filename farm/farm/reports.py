"""Report Generation Page - REQ-9.0"""
import reflex as rx
from .auth_utils import require_admin_only
from .db import get_all_orders, get_all_parcels, get_all_production_records

# --- COLOR DEFINITIONS ---
CROP_COLORS = {
    "Tomatoes": "#ef4444",       # Red
    "Crisp Lettuce": "#22c55e",  # Fresh Green
    "New Potatoes": "#493806",   # Golden Yellow
    "Organic Carrots": "#f97316",# Orange
    "Eggplants": "#8b5cf6",      # Purple
    "Cucumbers": "#10b981",      # Darker Green
    "Strawberries": "#e11d48",   # Berry Red
    "Onions": "#fef08a",         # Pale Yellow
    "Zucchini": "#05661D"
}

DEFAULT_COLORS = ["#f97316", "#22c55e","#493806", "#f43f5e", "#05661D"]


class ReportState(rx.State):  # pylint: disable=inherit-non-class
    financial_data: list[dict] = []
    total_revenue: str = "0.00 RON"
    crop_distribution: list[dict] = []
    production_history: list[dict] = [] # Added for REQ-9.2

    def load_financial_report(self):
        """Loads financials, crop distribution, and production history."""
        try:
            # 1. Load Financials (REQ-9.5)
            orders = get_all_orders()
            self.financial_data = orders
            
            total = 0.0
            for order in orders:
                if order.get("status") != "Cancelled":
                    price_str = str(order.get("total", "0")).replace(" RON", "")
                    try:
                        total += float(price_str)
                    except ValueError:
                        pass
            self.total_revenue = f"{total:.2f} RON"
            
            # 2. Load Crop Data for Chart (REQ-9.6)
            parcels = get_all_parcels()
            crop_counts = {}
            for p in parcels:
                crop_name = p.get("crop", "Unknown")
                crop_counts[crop_name] = crop_counts.get(crop_name, 0) + 1
            
            formatted_data = []
            color_index = 0
            for name, count in crop_counts.items():
                slice_color = CROP_COLORS.get(name)
                if not slice_color:
                    slice_color = DEFAULT_COLORS[color_index % len(DEFAULT_COLORS)]
                    color_index += 1
                
                formatted_data.append({
                    "name": name,
                    "value": count,
                    "fill": slice_color  
                })
            self.crop_distribution = formatted_data

            # 3. Load Production History (REQ-9.2)
            self.production_history = get_all_production_records()
            
        except Exception as e:
            print(f"Error loading reports: {e}")


def report_row(order: dict):
    """Generates a single row for the financial table."""
    return rx.table.row(
        rx.table.cell(order["id"].to(str)),
        rx.table.cell(order["timestamp"].to(str)),
        rx.table.cell(
            rx.badge(
                order["status"].to(str),
                color_scheme=rx.cond(order["status"] == "Pending", "orange", "green")
            )
        ),
        rx.table.cell(order["total"].to(str), weight="bold"),
    )

def history_row(record: dict):
    """Generates a single row for the production history table."""
    return rx.table.row(
        rx.table.cell(record["harvest_date"].to(str)),
        rx.table.cell(record["parcel_name"].to(str), weight="bold"),
        rx.table.cell(record["crop"].to(str)),
        rx.table.cell(record["actual_yield"].to(str) + " kg"),
        rx.table.cell(record["quality_notes"].to(str)),
        rx.table.cell(record["modified_by"].to(str)),
    )


@require_admin_only
def reports_page():
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Farm Financial & Production Reports", size="7", color="#2d5a27"),
                rx.spacer(),
                rx.button(
                    "Refresh Data", 
                    on_click=ReportState.load_financial_report, 
                    color_scheme="grass"
                ),
                width="100%"
            ),
            rx.divider(margin_y="20px"),
            
            # KPI Card
            rx.hstack(
                rx.card(
                    rx.vstack(
                        rx.text("Total Projected Revenue", size="3", color="gray"),
                        rx.text(ReportState.total_revenue, size="8", weight="bold", color="#2d5a27"),
                    ),
                    padding="20px",
                ),
                width="100%",
            ),

            # Graphical View (REQ-9.6)
            rx.heading("Crop Distribution on Parcels", size="5", margin_top="30px", color="#2d5a27"),
            rx.card(
                rx.recharts.pie_chart(
                    rx.recharts.pie(
                        data=ReportState.crop_distribution,
                        data_key="value",
                        name_key="name",
                        cx="50%",
                        cy="50%",
                        outer_radius=100,
                        label=True,
                    ),
                    rx.recharts.graphing_tooltip(),
                    rx.recharts.legend(),
                    width="100%",
                    height=300,
                ),
                width="100%",
                padding="20px",
                background_color="white",
            ),
            
            # Data Table (REQ-9.5)
            rx.heading("Customer Purchase History", size="5", margin_top="30px", color="#2d5a27"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Order ID"),
                        rx.table.column_header_cell("Date"),
                        rx.table.column_header_cell("Status"),
                        rx.table.column_header_cell("Total Price"),
                    ),
                ),
                rx.table.body(
                    rx.foreach(ReportState.financial_data, lambda order: report_row(order))
                ),
                width="100%",
                variant="surface",
            ),

            # Production History Table (REQ-9.2)
            rx.heading("Production History", size="5", margin_top="30px", color="#2d5a27"),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Harvest Date"),
                        rx.table.column_header_cell("Parcel Name"),
                        rx.table.column_header_cell("Crop Type"),
                        rx.table.column_header_cell("Actual Yield"),
                        rx.table.column_header_cell("Quality Notes"),
                        rx.table.column_header_cell("Harvested By"),
                        style={"background_color": "#2d5a27", "color": "white"}
                    ),
                ),
                rx.table.body(rx.foreach(ReportState.production_history, history_row)),
                width="100%", 
                variant="surface", 
                box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            ),
            
            # Navigation
            rx.link("← Back to Dashboard", href="/admin", color="gray", margin_top="20px"),
            
            width="100%",
            max_width="1000px",
            margin="auto",
            padding="40px",
        ),
        background_color="#f8fafc",
        min_height="100vh",
        on_mount=ReportState.load_financial_report
    )