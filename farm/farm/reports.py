"""Report Generation Page - REQ-9.0"""
import reflex as rx
from .auth_utils import require_admin_only
from .db import get_all_orders, get_all_parcels

class ReportState(rx.State):  # pylint: disable=inherit-non-class
    financial_data: list[dict] = []
    total_revenue: str = "0.00 RON"
    
    # New variable for the chart
    crop_distribution: list[dict] = []

    def load_financial_report(self):
        """REQ-9.5: Financial information represented in table form."""
        try:
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
            
            # REQ-9.6: Load and aggregate crop data
            parcels = get_all_parcels()
            distribution = {}
            for p in parcels:
                crop = p.get("crop", "Unassigned")
                distribution[crop] = distribution.get(crop, 0) + 1
                
            self.crop_distribution = [{"name": k, "value": v} for k, v in distribution.items()]
            
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

@require_admin_only
def reports_page():
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Farm Financial Reports", size="7", color="#2d5a27"),
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

            # Graphical View (REQ-9.6) - Recharts Pie Chart
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
                        fill="#4caf50", # Matches your green theme
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
                    # pylint: disable=no-value-for-parameter
                    rx.foreach(ReportState.financial_data, lambda order: report_row(order))
                ),
                width="100%",
                variant="surface",
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