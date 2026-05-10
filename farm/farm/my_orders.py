"""Customer Order Tracking Page"""
import reflex as rx
from farm.login import LoginState
from farm.db import get_orders_by_user, cancel_customer_order

class MyOrdersState(rx.State):
    my_orders: list[dict] = []

    async def load_orders(self):
        """Fetches orders only for the logged-in user."""
        login_state = await self.get_state(LoginState)
        if not login_state.is_authenticated:
            return rx.redirect("/login")
            
        # Fetch data and reverse so newest orders are at the top
        self.my_orders = get_orders_by_user(login_state.email)
        self.my_orders.reverse()

    async def cancel_order(self, order_id: str):
        """Allows cancellation if the order is still 'Created'."""
        success = cancel_customer_order(order_id)
        if success:
            await self.load_orders() # Refresh the list instantly
            return rx.toast.success("Order has been successfully cancelled.")
        return rx.toast.error("Cannot cancel this order. It may already be processing.")

def status_step(label: str, current_level: rx.Var, step_level: int):
    """Renders a single step in the tracking progress bar."""
    # FIX: Explicitly cast the Reflex Var to an integer for the comparison
    is_done = current_level.to(int) >= step_level

    return rx.vstack(
        rx.box(
            width="24px", height="24px", border_radius="50%",
            background_color=rx.cond(is_done, "#2d5a27", "#e2e8f0"),
            display="flex", align_items="center", justify_content="center"
        ),
        rx.text(label, size="2", weight="bold", color=rx.cond(is_done, "#1e293b", "#94a3b8")),
        align="center", spacing="2"
    )

def order_tracking_card(order: dict):
    """The detailed tracking view for a single order."""
    is_created = (order["status"] == "Created")
    is_cancelled = (order["status"] == "Cancelled")
    
    # Safely map the string status to a number for the progress bar
    current_level = rx.match(
        order["status"].to(str),
        ("Created", 1),
        ("Pending", 2),
        ("Processing", 3),
        ("Shipped", 4),
        ("Delivered", 5),
        0
    )
    
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.heading(f"Order #{order['id'].to(str)[:8].upper()}", size="5", color="#2d5a27"),
                    rx.text(f"Placed on: {order['timestamp'].to(str)}", size="2", color="gray"),
                    align_items="start"
                ),
                rx.spacer(),
                rx.badge(
                    order["status"].to(str), 
                    color_scheme=rx.cond(is_cancelled, "red", rx.cond(is_created, "blue", "grass")),
                    size="2"
                ),
                width="100%", align_items="center"
            ),
            
            rx.divider(margin_y="15px"),
            
            # --- FULL TRACKING PROGRESS BAR ---
            rx.cond(
                ~is_cancelled,
                rx.hstack(
                    status_step("Ordered", current_level, 1),
                    rx.box(flex="1", height="4px", background_color="#e2e8f0", border_radius="2px", margin_top="12px"),
                    status_step("Confirmed", current_level, 2),
                    rx.box(flex="1", height="4px", background_color="#e2e8f0", border_radius="2px", margin_top="12px"),
                    status_step("Processing", current_level, 3),
                    rx.box(flex="1", height="4px", background_color="#e2e8f0", border_radius="2px", margin_top="12px"),
                    status_step("Shipped", current_level, 4),
                    rx.box(flex="1", height="4px", background_color="#e2e8f0", border_radius="2px", margin_top="12px"),
                    status_step("Delivered", current_level, 5),
                    width="100%", padding_y="20px", align_items="center"
                ),
                rx.center(rx.text("This order was cancelled.", color="red", weight="bold"), padding_y="20px", width="100%")
            ),
            
            rx.divider(margin_y="15px"),
            
            rx.hstack(
                rx.text(f"Order Total: {order['total'].to(str)} RON", size="4", weight="bold", color="#1e293b"),
                rx.spacer(),
                rx.cond(
                    is_created,
                    rx.button("Cancel Order", size="2", color_scheme="red", variant="soft", 
                              on_click=lambda: MyOrdersState.cancel_order(order["id"].to(str)))
                ),
                width="100%", align_items="center"
            ),
            width="100%"
        ),
        width="100%", margin_bottom="20px", border="1px solid #e2e8f0", padding="25px", box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1)"
    )

def my_orders_page():
    return rx.box(
        # Simple Header
        rx.hstack(
            rx.heading("🚜 My Order Tracking", size="6", color="white"),
            rx.spacer(),
            rx.button("← Back to Store", on_click=rx.redirect("/"), color_scheme="gray", variant="solid"),
            width="100%", padding="15px 30px", background_color="#2d5a27", align_items="center"
        ),
        
        # Main Content
        rx.vstack(
            rx.heading("Order History & Live Tracking", size="7", color="#fafafa", margin_bottom="10px"),
            rx.text("Track the progress of your farm-fresh deliveries in real time.", color="white", margin_bottom="30px"),
            
            rx.cond(
                MyOrdersState.my_orders.length() > 0,
                rx.vstack(
                    rx.foreach(MyOrdersState.my_orders, order_tracking_card),
                    width="100%"
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("package-search", size=60, color="#cbd5e1"),
                        rx.heading("No orders found", size="5", color="#64748b"),
                        rx.text("Looks like you haven't bought anything yet.", color="gray"),
                        rx.button("Start Shopping", on_click=rx.redirect("/"), margin_top="15px", color_scheme="grass"),
                        align_items="center"
                    ), padding="60px", width="100%"
                )
            ),
            width="100%", max_width="900px", margin="0 auto", padding="40px"
        ),
        on_mount=MyOrdersState.load_orders,
        background_image="url('/Iarba.png')",
        background_size="cover",
        background_position="center",
        background_attachment="fixed",
        box_shadow="inset 0 0 0 2000px rgba(0, 0, 0, 0.5)", 
        min_height="100vh",
    )