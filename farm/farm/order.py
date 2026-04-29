"""Checkout and Order Confirmation Page"""
import reflex as rx
from farm.store import StoreState
from farm.db import Database
from farm.login import LoginState

class OrderState(rx.State):
    """Handles the checkout process."""
    is_processing: bool = False
    order_successful: bool = False

    async def check_auth(self):
        """Redirects unauthenticated users to the login page immediately upon loading."""
        login_state = await self.get_state(LoginState)
        if not login_state.is_authenticated:
            return rx.redirect("/login")

    async def place_order(self):
        """Processes the cart and sends it to the staff database."""
        login_state = await self.get_state(LoginState)
        if not login_state.is_authenticated:
            return rx.redirect("/login")
        self.is_processing = True
        self.order_successful = False
        
        # Pull the cart data from the Storefront state
        store_state = await self.get_state(StoreState)
        
        if not store_state.cart:
            self.is_processing = False
            return rx.toast.error("Your cart is empty.")

        # CRITICAL FIX: Deep unpack the Reflex MutableProxy into raw Python types
        clean_cart = []
        for item in store_state.cart:
            clean_cart.append({
                "name": str(item["name"]),
                "price": str(item["price"]),
                "quantity": int(item["quantity"]),
                "total": float(item["total"])
            })
        
        # Save to database using the completely clean list
        success = Database.create_order(
            cart_items=clean_cart,
            total_price=str(store_state.formatted_total_price)
        )

        if success:
            store_state.cart = []
            self.order_successful = True
            rx.toast.success("Order placed!")
        else:
            rx.toast.error("Database connection failed. Please try again.")
            
        self.is_processing = False
def cart_item_row(item: dict, index: int):
    """Displays a single row in the checkout summary."""
    return rx.table.row(
        rx.table.cell(item["name"].to(str), font_weight="bold"),
        rx.table.cell(item["quantity"].to(str)),
        rx.table.cell(item["price"].to(str)),
        rx.table.cell(f"{item['total'].to(str)} RON", font_weight="bold"),
        rx.table.cell(
            rx.button(
                rx.icon("trash-2", size=16), 
                on_click=lambda: StoreState.remove_item(index),
                color_scheme="red", 
                variant="ghost"
            )
        )
    )

def order_page():
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.image(src="/Logo.ico", height="40px", width="auto"),
                rx.heading("Checkout", size="7", color="#2d5a27"),
                rx.spacer(),
                rx.button("← Back to Store", on_click=rx.redirect("/"), variant="outline", color_scheme="gray"),
                width="100%",
                align_items="center",
                padding_bottom="20px",
                border_bottom="1px solid #e2e8f0"
            ),
            
            # Success Message
            rx.cond(
                OrderState.order_successful,
                rx.callout(
                    "Order placed successfully! Our staff is currently processing it.",
                    icon="check-circle",
                    color_scheme="green",
                    width="100%",
                    margin_y="20px"
                )
            ),

            rx.cond(
                StoreState.cart_count > 0,
                # --- CART HAS ITEMS ---
                rx.vstack(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Product"),
                                rx.table.column_header_cell("Quantity"),
                                rx.table.column_header_cell("Unit Price"),
                                rx.table.column_header_cell("Total"),
                                rx.table.column_header_cell("Action"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(StoreState.cart, lambda item, i: cart_item_row(item, i))
                        ),
                        width="100%",
                        variant="surface"
                    ),
                    
                    rx.divider(margin_y="20px"),
                    
                    rx.hstack(
                        rx.heading("Total Amount:", size="5"),
                        rx.spacer(),
                        rx.heading(StoreState.formatted_total_price, size="6", color="#2d5a27"),
                        width="100%"
                    ),
                    
                    rx.button(
                        "Confirm & Place Order",
                        on_click=OrderState.place_order,
                        loading=OrderState.is_processing,
                        size="4",
                        width="100%",
                        color_scheme="grass",
                        margin_top="20px"
                    ),
                    width="100%"
                ),
                
                # --- CART IS EMPTY ---
                rx.center(
                    rx.vstack(
                        rx.icon("shopping-cart", size=60, color="#cbd5e1"),
                        rx.heading("Your cart is empty", size="5", color="#64748b"),
                        rx.button("Browse Products", on_click=rx.redirect("/"), margin_top="10px"),
                        align_items="center"
                    ),
                    padding="50px",
                    width="100%"
                )
            ),
            
            width="100%",
            max_width="800px",
            margin="0 auto",
            padding="40px",
            background_color="white",
            border_radius="12px",
            box_shadow="0 10px 15px -3px rgba(0, 0, 0, 0.1)",
            margin_top="40px"
        ),
        background_color="#f8fafc",
        min_height="100vh"
    )