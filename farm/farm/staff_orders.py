"""Staff Page to manage customer orders - REQ-6.2"""
import reflex as rx
from .db import get_all_orders, update_order_status, delete_order
from typing import List, Dict, Any
from farm.login import LoginState
from .store import StoreState

class StaffOrderState(rx.State):
    orders: list[dict] = []
    is_loading: bool = True
    search_query: str = ""
   

    def fetch_orders(self):
        try:
            self.orders = get_all_orders()
        except Exception as e:
            print(f"Error: {e}")
    
    def set_order_status(self, new_status: str, order_id: str):
        """Updates the status based on the dropdown selection."""
        update_order_status(order_id, new_status)
        self.fetch_orders() # Refresh UI

    def remove_order(self, order_id: str):
        """Deletes the order from the database."""
        delete_order(order_id)
        self.fetch_orders() # Refresh UI

    def change_status(self, order_id: str, current_status: str):
        status_flow = {"Created": "Pending", "Pending": "Shipped", "Shipped": "Delivered", "Delivered": "Pending"}
        new_status = status_flow.get(current_status, "Pending")
        update_order_status(order_id, new_status)
        self.fetch_orders()

    @rx.var
    def filtered_orders(self) -> list[dict]:
        """REQ-8.5 & REQ-8.6: Case insensitive search by status and date."""
        if not self.search_query:
            return self.orders
        
        query = self.search_query.lower().strip()
        # Permitem caracterele folosite în date (cratimă, punct, două puncte, slash)
        query = "".join(e for e in query if e.isalnum() or e.isspace() or e in "-/.:")
        
        return [
            o for o in self.orders 
            if query in str(o.get("status", "")).lower()
            or query in str(o.get("timestamp", "")).lower() # NOU: Căutare după dată
        ]

def staff_navbar():
    """Bara de navigare superioară dedicată paginilor de Staff."""
    return rx.hstack(
        # Partea stângă: Logo și Titlu
        rx.hstack(
            rx.image(src="/Logo.ico", height="40px", width="auto", border_radius="4px"),
            rx.heading("Farm Management", size="6", color="white"),
            spacing="3",
            align_items="center",
        ),
        rx.spacer(),
        # Partea dreaptă: Info user și Logout
        rx.hstack(
            rx.text(f"Operator: {LoginState.user_name}", color="#deff9a", weight="bold"),
            rx.button("Logout", on_click=LoginState.logout, color_scheme="red", variant="solid"),
            spacing="4",
            align_items="center",
        ),
        width="100%",
        padding="15px 30px",
        background_color="#2d5a27", # Verdele principal pentru contrast
        box_shadow="0 4px 10px rgba(0,0,0,0.1)",
    )

def order_card(order: rx.Var[Dict[str, Any]]):
    """Order card with dropdown status, visual confirmation, and delete button."""
    is_created = (order["status"] == "Created")
    
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(f"Date: {order['timestamp'].to(str)}", size="2", color="#64748b", weight="bold"),
                rx.spacer(),
                
                # REQ-7.8: Visual Confirmation Button
                rx.cond(
                    is_created,
                    rx.button(
                        "Confirm Order",
                        color_scheme="green",
                        size="1",
                        cursor="pointer",
                        on_click=lambda: StaffOrderState.set_order_status("Processing", order["id"].to(str))
                    )
                ),
                
                # Delete Button
                rx.button(
                    rx.icon("trash-2", size=16),
                    on_click=lambda: StaffOrderState.remove_order(order["id"].to(str)),
                    color_scheme="red",
                    variant="ghost",
                    size="1",
                    cursor="pointer"
                ),
                width="100%",
                align_items="center",
                spacing="3"
            ),
            rx.divider(margin_y="10px"),
            
            # List of items in the order
            rx.vstack(
                rx.foreach(
                    order["items"].to(List[Dict[str, Any]]), 
                    lambda item: rx.hstack(
                        rx.text(item["name"].to(str), size="3", color="#1e293b", weight="medium"),
                        rx.spacer(),
                        rx.text(item["price"].to(str), size="3", color="#2d5a27", weight="bold"),
                        width="100%"
                    )
                ),
                width="100%",
            ),
            rx.divider(margin_y="10px"),
            
            # Status Dropdown
            rx.hstack(
                rx.text("Status:", size="2", weight="bold", color="#1e293b"),
                rx.select(
                    ["Created", "Pending", "Processing", "Shipped", "Delivered", "Cancelled"],
                    value=order["status"].to(str),
                    on_change=lambda value: StaffOrderState.set_order_status(value, order["id"].to(str)),
                    width="100%",
                    color_scheme="grass"
                ),
                width="100%",
                align_items="center",
                spacing="3"
            ),
        ),
        background_color="white",
        padding="20px",
        border="1px solid #e2e8f0",
        box_shadow="0 10px 15px -3px rgba(0, 0, 0, 0.1)",
        border_radius="12px",
    )

def staff_orders_page():
    return rx.box(
        on_mount=StaffOrderState.check_permissions,
        width="100%",
        min_height="100vh",
        background_color="#f8fafc", # Fundalul rămâne gri deschis, dar acum elementele de deasupra sunt clare
    )