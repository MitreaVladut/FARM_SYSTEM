"""Staff Page to manage customer orders - REQ-6.2"""
import reflex as rx
from .db import get_all_orders, update_order_status
from typing import List, Dict, Any
from .store import StoreState

class StaffOrderState(rx.State):
    orders: list[dict] = []
    is_loading: bool = True

    async def check_permissions(self):
        """The Hard Lock Gatekeeper."""
        self.is_loading = True
        store = await self.get_state(StoreState)
        
        # If the role isn't exactly what we require, kick them out immediately
        if not store.authenticated or store.user_role not in ["Staff", "Admin"]:
            return rx.redirect("/login")
        
        # Only if they have the credentials, we allow the fetch
        self.fetch_orders()
        self.is_loading = False

    def fetch_orders(self):
        try:
            self.orders = get_all_orders()
        except Exception as e:
            print(f"Error: {e}")

    def change_status(self, order_id: str, current_status: str):
        status_flow = {"Pending": "Shipped", "Shipped": "Delivered", "Delivered": "Pending"}
        new_status = status_flow.get(current_status, "Pending")
        update_order_status(order_id, new_status)
        self.fetch_orders()

def order_card(order: rx.Var[Dict[str, Any]]):
    """Template for an order card."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(f"Order Date: {order['timestamp'].to(str)}", size="2"),
                rx.spacer(),
                rx.badge(order["status"].to(str), color_scheme="green"),
                width="100%",
            ),
            rx.divider(),
            rx.vstack(
                rx.foreach(
                    order["items"].to(List[Dict[str, Any]]), 
                    lambda item: rx.hstack(
                        rx.text(item["name"].to(str), size="2"),
                        rx.spacer(),
                        rx.text(item["price"].to(str), size="2"),
                        width="100%"
                    )
                ),
                width="100%",
            ),
            rx.divider(),
            rx.button(
                "Update Status", 
                on_click=lambda: StaffOrderState.change_status(order["id"].to(str), order["status"].to(str)),
                width="100%"
            ),
        )
    )

def staff_orders_page():
    return rx.center(
        # The condition: Is the user authenticated AND are they Staff/Admin?
        rx.cond(
            StoreState.authenticated & ( (StoreState.user_role == "Staff") | (StoreState.user_role == "Admin") ),
            # --- THE ACTUAL STAFF CONTENT ---
            rx.vstack(
                rx.hstack(
                    rx.heading("Staff Dashboard - Orders", size="7"),
                    rx.spacer(),
                    rx.button("Logout", on_click=StoreState.logout, color_scheme="red"),
                    width="100%",
                ),
                rx.grid(
                    rx.foreach(StaffOrderState.orders, order_card),
                    columns="3",
                    spacing="4",
                    width="100%",
                ),
                padding="40px",
                width="100%",
            ),
            # --- THE 'YOU DON'T BELONG HERE' VIEW ---
            rx.vstack(
                rx.spinner(),
                rx.text("Verifying Staff Credentials..."),
                height="100vh",
                justify="center",
            )
        ),
        on_mount=StaffOrderState.check_permissions,
        width="100%",
        min_height="100vh",
        background_color="#f8fafc",
    )