"""Staff Page to manage customer orders - REQ-6.2"""
import reflex as rx
from .db import get_all_orders, update_order_status, delete_order
from typing import List, Dict, Any
from farm.login import LoginState

class StaffOrderState(rx.State):
    orders: list[dict] = []
    is_loading: bool = True

    async def check_permissions(self):
        self.is_loading = True
        login_state = await self.get_state(LoginState)
        
        if not login_state.is_authenticated or login_state.user_role not in ["Staff", "Admin"]:
            return rx.redirect("/login")
        
        self.fetch_orders()
        self.is_loading = False

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
        status_flow = {"Pending": "Shipped", "Shipped": "Delivered", "Delivered": "Pending"}
        new_status = status_flow.get(current_status, "Pending")
        update_order_status(order_id, new_status)
        self.fetch_orders()

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
    """Order card with dropdown status and delete button."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(f"Date: {order['timestamp'].to(str)}", size="2", color="#64748b", weight="bold"),
                rx.spacer(),
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
                align_items="center"
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
                    ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"],
                    value=order["status"].to(str),
                    # When dropdown changes, send the new value and the order ID to the state
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
        rx.cond(
            LoginState.is_authenticated & ( (LoginState.user_role == "Staff") | (LoginState.user_role == "Admin") ),
            
            # --- CONȚINUTUL VIZIBIL ---
            rx.vstack(
                staff_navbar(), # Adăugăm noul header cu logo
                
                rx.vstack(
                    rx.hstack(
                        rx.heading("Procesare Comenzi", size="8", color="#2d5a27"), # Contrast fixat
                        rx.spacer(),
                        rx.link(
                            rx.button("← Înapoi la Panou", variant="outline", color_scheme="gray"), 
                            href="/staff"
                        ),
                        width="100%",
                        align_items="center",
                        margin_bottom="20px"
                    ),
                    
                    rx.grid(
                        rx.foreach(StaffOrderState.orders, order_card),
                        columns="3",
                        spacing="5",
                        width="100%",
                    ),
                    padding="40px",
                    width="100%",
                    max_width="1400px",
                    margin="0 auto"
                ),
            ),
            
            # --- ECRAN DE ÎNCĂRCARE ---
            rx.center(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text("Se verifică permisiunile...", color="#1e293b"),
                ),
                height="100vh"
            )
        ),
        on_mount=StaffOrderState.check_permissions,
        width="100%",
        min_height="100vh",
        background_color="#f8fafc", # Fundalul rămâne gri deschis, dar acum elementele de deasupra sunt clare
    )