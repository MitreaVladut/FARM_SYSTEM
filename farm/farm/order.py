import reflex as rx
from farm.store import StoreState

def cart_item(item, index):
    """The individual row for each product in the cart."""
    return rx.hstack(
        # LEFT SIDE: Product Info
        rx.vstack(
            rx.text(item["name"], size="3", weight="bold", color="#2d5a27"), # Dark Green
            rx.text(f"Qty: {item['quantity']}", size="2", color="#666"), # Explicit Gray
            align_items="start",
            spacing="0",
        ),
        rx.spacer(),
        # RIGHT SIDE: Price and Trash
        rx.hstack(
            rx.text(f"{item['total']:.2f} RON", weight="bold", color="#c2410c"), # Orange
            rx.icon(
                "trash-2", 
                size=20, 
                color="#e11d48", # Red
                cursor="pointer",
                on_click=lambda: StoreState.remove_item(index) # pylint: disable=no-value-for-parameter
            ),
            spacing="4",
            align="center",
        ),
        width="100%",
        padding_y="12px",
        border_bottom="1px solid #eee",
    )

# pylint: disable=not-callable
@rx.page(route="/order")
def order_page():
    return rx.center(
        rx.vstack(
            rx.heading("Your Order Summary", size="6", color="#2d5a27", margin_bottom="10px"),
            
            # THE LIST OF ITEMS
            rx.box(
                rx.cond(
                    StoreState.cart_count > 0,
                    rx.vstack(
                        rx.foreach(StoreState.cart, lambda item, index: cart_item(item, index)),
                        width="100%",
                    ),
                    rx.text("Your cart is currently empty.", color="gray", italic=True)
                ),
                width="100%",
                background="white",
                padding_x="20px",
            ),

            rx.divider(margin_y="15px"),

            # TOTAL SECTION
            rx.hstack(
                rx.text("Total Amount:", size="4", weight="bold", color="#444"),
                rx.spacer(),
                rx.text(
                    StoreState.formatted_total_price, 
                    size="6", 
                    weight="bold", 
                    color="#2d5a27"
                ),
                width="100%",
                padding_x="20px",
            ),

            # ACTION BUTTON
            rx.button(
                "Confirm Order",
                on_click=rx.toast.success("Order Placed!"), # Replace with actual logic later
                width="100%",
                size="3",
                background_color="#2d5a27",
                color="white",
                margin_top="15px",
                _hover={"background_color": "#1e3a1a"}
            ),
            
            rx.link("← Back to Store", href="/", color="gray", size="2"),

            width="450px",
            padding="30px",
            border_radius="15px",
            box_shadow="0px 4px 20px rgba(0, 0, 0, 0.1)",
            background_color="white",
            align="center",
        ),
        padding_y="50px",
        background_color="#4e9262", # Light gray background so the white card pops
        min_height="100vh",
    )