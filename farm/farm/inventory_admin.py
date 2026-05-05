"""Staff Inventory Management Page - REQ-4.1 & REQ-4.9"""
import reflex as rx
from .db import get_all_inventory, update_inventory_item

class InventoryState(rx.State):  
    items: list[dict] = []

    def fetch_items(self):
        """Load all products from MongoDB."""
        try:
            self.items = get_all_inventory()
        except Exception as e:
            print(f"Error: {e}")

    # --- NEW: Logistics Tracking (REQ-4.9) ---
    def update_location(self, item_name: str, new_location: str):
        """Tracks the physical movement of goods through the warehouse."""
        update_inventory_item(item_name, {"location": new_location})
        self.fetch_items()
        return rx.toast.info(f"Moved {item_name} to {new_location}.")

    def update_status(self, item_name: str, new_status: str):
        """Updates the QA/Availability status of the goods."""
        update_inventory_item(item_name, {"status": new_status})
        self.fetch_items()
        return rx.toast.info(f"Status of {item_name} changed to {new_status}.")
    # -----------------------------------------

def inventory_row(product: dict):
    """Render a single row in the inventory table."""
    return rx.table.row(
        rx.table.cell(product["name"].to(str), weight="bold"),
        rx.table.cell(
            rx.hstack(
                rx.text(product["stock"].to(str), weight="bold", color="#2d5a27"),
                rx.text(product.get("unit", "kg").to(str), color="gray")
            )
        ),
        rx.table.cell(rx.text("$", product.get("price", "0").to(str))),
        
        # REQ-4.9: Warehouse Location Dropdown
        rx.table.cell(
            rx.select(
                ["Receiving Bay", "Cold Storage A", "Cold Storage B", "Dry Warehouse 1", "Shipping Dock"],
                value=product.get("location", "Receiving Bay").to(str),
                on_change=lambda val: InventoryState.update_location(product["name"].to(str), val),
                color_scheme="blue",
            )
        ),
        
        # REQ-4.9: QA Status Dropdown (Upgraded from the old Toggle button)
        rx.table.cell(
            rx.select(
                ["Pending QA", "In Stock", "Quarantined", "Out of Stock"],
                value=product.get("status", "Pending QA").to(str),
                on_change=lambda val: InventoryState.update_status(product["name"].to(str), val),
                color_scheme=rx.cond(product.get("status", "") == "In Stock", "green", "orange"),
            )
        ),
    )

def inventory_admin_page():
    """The main UI for Staff to manage farm output and logistics."""
    return rx.vstack(
        rx.hstack(
            rx.heading("📦 Warehouse & Inventory Dashboard", size="7", color="#2d5a27"),
            rx.spacer(),
            rx.button(
                "Refresh Data", 
                on_click=InventoryState.fetch_items,
                color_scheme="grass",
                variant="soft"
            ),
            width="100%",
            padding_bottom="10px",
            align_items="center",
        ),
        rx.text("Track storage levels, physical warehouse locations, and QA status.", color="gray", margin_bottom="20px"),
        
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Product"),
                    rx.table.column_header_cell("Stock Level"),
                    rx.table.column_header_cell("Price"),
                    rx.table.column_header_cell("Warehouse Location"), # NEW
                    rx.table.column_header_cell("QA Status"),          # UPGRADED
                    style={"background_color": "#2d5a27", "color": "white"}
                ),
            ),
            rx.table.body(
                rx.foreach(InventoryState.items, inventory_row)
            ),
            width="100%",
            variant="surface",
            box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1)"
        ),
        on_mount=InventoryState.fetch_items,
        padding="40px",
        width="100%",
        min_height="100vh",
        background_color="#f8fafc",
    )