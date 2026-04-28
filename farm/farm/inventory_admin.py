"""Staff Inventory Management Page - REQ-4.1"""
import reflex as rx
from .db import get_all_inventory, update_inventory_item

class InventoryState(rx.State):  # pylint: disable=inherit-non-class
    items: list[dict] = []

    def fetch_items(self):
        """Load all products from MongoDB."""
        try:
            self.items = get_all_inventory()
        except Exception as e:
            print(f"Error: {e}")

    def toggle_status(self, product_name: str):
        """Toggle status using the name as a unique identifier."""
        # Find the product in the current state list
        product = next((item for item in self.items if item["name"] == product_name), None)
        
        if product:
            new_status = "Out of Stock" if product["status"] == "In Stock" else "In Stock"
            # Update the specific field in MongoDB
            update_inventory_item(product_name, {"status": new_status})
            # Refresh the table data
            self.fetch_items()

def inventory_row(product: dict):
    """Render a single row in the inventory table."""
    return rx.table.row(
        rx.table.cell(product["name"]),
        rx.table.cell(product["stock"]),
        rx.table.cell(product["price"]),
        rx.table.cell(
            rx.badge(
                product["status"],
                # Use rx.cond for client-side reactive coloring
                color_scheme=rx.cond(product["status"] == "In Stock", "green", "red"),
            )
        ),
        rx.table.cell(
            rx.button(
                "Toggle Status",
                size="1",
                # Pass the string name directly to the state method
                on_click=lambda: InventoryState.toggle_status(product["name"]), # pylint: disable=no-value-for-parameter
                variant="surface",
            )
        ),
    )

def inventory_admin_page():
    """The main UI for Staff to manage farm output."""
    return rx.vstack(
        rx.hstack(
            rx.heading("Staff Inventory Dashboard", size="7", color="#2d5a27"),
            rx.spacer(),
            rx.button(
                "Refresh Data", 
                on_click=InventoryState.fetch_items,
                color_scheme="grass",
                variant="soft"
            ),
            width="100%",
            padding_bottom="20px",
            align_items="center",
        ),
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Product"),
                    rx.table.column_header_cell("Stock Level"),
                    rx.table.column_header_cell("Price"),
                    rx.table.column_header_cell("Status"),
                    rx.table.column_header_cell("Actions"),
                ),
            ),
            rx.table.body(
                rx.foreach(InventoryState.items, inventory_row)
            ),
            width="100%",
            variant="surface",
        ),
        on_mount=InventoryState.fetch_items,
        padding="40px",
        width="100%",
        min_height="100vh",
        background_color="#f8fafc",
    )