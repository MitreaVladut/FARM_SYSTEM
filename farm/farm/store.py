"""Customer Storefront Page for Farm Management System"""
import reflex as rx
from .db import get_all_inventory  # Import your new db helper
import re # Add this import at the top of store.py
from farm.login import LoginState # <-- Importul adăugat pentru a citi starea de logare

class StoreState(rx.State):  # pylint: disable=inherit-non-class
    """Handle search and order logic for customers."""
    search_value: str = ""
    raw_inventory: list[dict] = []
    authenticated: bool = False
    user_role: str = ""
    
    # Cart and Modal Logic
    cart: list[dict] = [] 
    show_dialog: bool = False
    selected_product: dict = {}
    quantity_to_add: str = "1"  # Keep as string for the input box
    error_message: str = ""

    @rx.var
    def cart_total_price(self) -> float:
        """Sum up the 'total' field of every item in the cart dictionary."""
        return sum(item["total"] for item in self.cart)

    @rx.var
    def formatted_total_price(self) -> str:
        """Formats the sum as a readable string for the UI."""
        return f"{self.cart_total_price:.2f} RON"

    def remove_item(self, index: int):
        """Logic for the trash can: removes item by its list position."""
        self.cart.pop(index)
        
    def logout(self):
        """Reset everything on logout."""
        self.authenticated = False
        self.user_role = ""
        return rx.redirect("/login")
    
  

    def select_product(self, product: dict):
        """Opens the window and resets values for the chosen product."""
        self.selected_product = product
        self.quantity_to_add = "1"
        self.error_message = ""
        self.show_dialog = True

    def close_dialog(self):
        self.show_dialog = False

    def add_to_cart(self):
        try:
            qty = int(self.quantity_to_add)
        
            # 1. Clean the Price (e.g., "17 RON / kg" -> 17.0)
            # This regex finds the first number (including decimals) in the string
            price_match = re.search(r"(\d+(\.\d+)?)", str(self.selected_product.get("price", "0")))
            unit_price = float(price_match.group(1)) if price_match else 0.0

            # 2. Clean the Stock (e.g., "180 kg" or "8 pieces" -> 180 or 8)
            stock_match = re.search(r"(\d+)", str(self.selected_product.get("stock", "0")))
            current_stock = int(stock_match.group(1)) if stock_match else 0

            # 3. Validation
            if qty <= 0:
                self.error_message = "Quantity must be at least 1."
                return
            if qty > current_stock:
                self.error_message = f"Only {current_stock} available!"
                return

            # 4. Add to list with math already done
            self.cart.append({
                "name": self.selected_product["name"],
                "price": self.selected_product["price"], # Keep the string for display
                "quantity": qty,
                "total": unit_price * qty # This is a pure float for the Order page
            })
        
            self.show_dialog = False
            return rx.toast.success(f"Added {qty} units to cart!")

        except Exception as e:
            self.error_message = f"Calculation error: {str(e)}"

    @rx.var
    def cart_count(self) -> int:
        return len(self.cart)

    def fetch_inventory(self):
        """Called when the page loads to pull data from MongoDB."""
        try:
            self.raw_inventory = get_all_inventory()
        except Exception as e:
            print(f"Error connecting to DB: {e}")

    @rx.var
    def filtered_inventory(self) -> list[dict]:
        """REQ-8.6, REQ-8.7: Filters the DB results securely and case-insensitively."""
        
        # 1. Sanitize Input (REQ-8.7): 
        safe_search = re.sub(r'[^a-zA-Z0-9\s]', '', self.search_value)
        
        # 2. Case-Insensitive (REQ-8.6): 
        search_query = safe_search.strip().lower()
        
        # Sort inventory alphabetically
        items = sorted(self.raw_inventory, key=lambda x: x.get("name", ""))
        
        if not search_query:
            return items
            
        # 3. Compare the safe, lowercase search query against the lowercase product names
        return [
            item for item in items 
            if search_query in str(item.get("name", "")).lower()
        ]

    @rx.var
    def has_results(self) -> bool:
        """Helper to determine if products exist after filtering."""
        return len(self.filtered_inventory) > 0
    
    my_orders: list[dict] = []
    show_orders_modal: bool = False

    async def load_my_orders(self):
        """Fetches orders for the logged-in user."""
        # 1. Safely check the actual LoginState
        login_state = await self.get_state(LoginState)
        if not login_state.is_authenticated:
            return rx.toast.error("You must be logged in to view orders.")
            
        # 2. Fetch data and open the modal
        from .db import get_all_orders 
        all_orders = get_all_orders()
        self.my_orders = [o for o in all_orders if o.get("status") in ["Created", "Cancelled"]]
        self.show_orders_modal = True

    async def cancel_my_order(self, order_id: str):
        from .db import cancel_customer_order
        success = cancel_customer_order(order_id)
        if success:
            await self.load_my_orders() # Refresh list
            return rx.toast.success("Order has been successfully cancelled.")
        return rx.toast.error("Cannot cancel this order (it may already be processed).")
    

def quantity_dialog():
    """The pop-up window for quantity selection."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(f"Order {StoreState.selected_product['name']}"),
                rx.hstack(
                    rx.text("Price per unit:", weight="bold"),
                    rx.text(StoreState.selected_product["price"]),
                    justify="between", width="100%"
                ),
                rx.hstack(
                    rx.text("Available in storage:", weight="bold"),
                        rx.badge(
                            # Change this to "stock" to match your DB
                            StoreState.selected_product["stock"].to(str), 
                            color_scheme="blue"
                        ),
                    justify="between", width="100%"
                ),
                rx.divider(),
                rx.text("How much would you like to order?", size="2"),
                rx.input(
                    placeholder="Enter quantity",
                    value=StoreState.quantity_to_add,
                    on_change=StoreState.set_quantity_to_add,
                    type="number",
                    width="100%",
                ),
                rx.cond(
                    StoreState.error_message != "",
                    rx.text(StoreState.error_message, color="red", size="2", weight="bold"),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Cancel", variant="soft", color_scheme="gray")
                    ),
                    rx.button(
                        "Confirm Add", 
                        on_click=StoreState.add_to_cart,
                        background_color="#2d5a27",
                        color="white"
                    ),
                    spacing="3",
                    margin_top="10px",
                ),
                spacing="4",
            ),
            max_width="350px",
        ),
        open=StoreState.show_dialog,
        on_open_change=StoreState.set_show_dialog,
    )
    

def product_card(product: rx.Var[dict]):
    is_out_of_stock = (product["status"] == "Out of Stock")
    
    return rx.card(
        rx.vstack(
            rx.image(
                src=product["image"], 
                width="100%", height="160px", object_fit="cover", border_radius="10px"
            ),
            rx.vstack(
                rx.text(product["name"], size="4", weight="bold", color="#1e293b"),
                rx.text(product["price"], size="3", weight="bold", color="#2d5a27"),
                
                # REQ-5.2: Clearly display remaining quantities in stock
                rx.badge(
                    "Remaining Stock: ", product["stock"], 
                    color_scheme=rx.cond(is_out_of_stock, "red", "blue"),
                    variant="soft"
                ),
                
                align_items="start", spacing="1", width="100%",
            ),
            rx.button(
                rx.cond(is_out_of_stock, "Out of Stock", "Add to Cart"),
                on_click=lambda: StoreState.select_product(product),
                width="100%",
                style={
                    "background_color": rx.cond(is_out_of_stock, "#b10000", "#2d5a27"),
                    "color": "white",
                    "font_weight": "bold",
                    "_hover": {"transform": "scale(1.02)", "transition": "0.2s"}
                },
                disabled=is_out_of_stock,
            ),
            spacing="3",
        ),
        width="240px", padding="12px", background_color="white",
        border="1px solid #e2e8f0", box_shadow="0 10px 15px -3px rgba(0, 0, 0, 0.1)",
    )

def navbar():
    """Bara de navigare reactivă - înlocuiește vechiul header static."""
    return rx.hstack(
        rx.heading("🚜 Farm Store", size="6", color="white"),
        rx.spacer(),
        
        # Verificăm dinamic dacă utilizatorul este logat folosind LoginState
        rx.cond(
            LoginState.is_authenticated,
            
            # UI pentru utilizator CONECTAT (afișăm numele și butoanele de profil)
            rx.hstack(
                rx.text("Hello, ", LoginState.user_name, "!", weight="bold", color="white"),

                rx.button("My Orders", on_click=rx.redirect("/my-orders"), color_scheme="blue", variant="solid"), 
                
                # Afișăm butonul către panoul de control DOAR pentru Admin sau Staff
                rx.cond(
                    LoginState.user_role == "Admin",
                    rx.button("Admin Panel", on_click=rx.redirect("/admin"), color_scheme="gray", variant="solid"),
                    rx.cond(
                        LoginState.user_role == "Staff",
                        rx.button("Staff Panel", on_click=rx.redirect("staff"), color_scheme="gray", variant="solid"),
                        rx.fragment() # Nu afișăm nimic în plus pentru rolul "Customer"
                    )
                ),
                
                rx.button("Logout", on_click=LoginState.logout, color_scheme="red", variant="solid"),
                align_items="center",
                spacing="4"
            ),
            
            # UI pentru vizitator NECONECTAT (doar butonul de Login)
            rx.button("Login", on_click=rx.redirect("/login"), size="2", variant="solid", background_color="white", color="#2d5a27")
        ),
        
        width="100%",
        padding="15px 30px",
        background_color="#2d5a27", # Păstrăm tema verde
        align_items="center"
    )
    
def farm_info_banner():
    """REQ-5.4: Displays information about the producing farm."""
    return rx.card(
        rx.hstack(
            rx.icon("tractor", size=40, color="#2d5a27"),
            rx.vstack(
                rx.heading("About Our Farm", size="5", color="#2d5a27"),
                rx.text(
                    "Located in Romania, our farm spans over many hectares "
                    "of rich, fertile soil. We are committed to sustainable, eco-friendly agriculture, "
                    "bringing organic, locally-grown produce straight from our fields to your table.",
                    color="gray", size="2"
                ),
                align_items="start"
            ),
            spacing="4", align_items="center"
        ),
        width="100%", margin_top="20px", padding="20px", background_color="#f0fdf4", border="1px solid #bbf7d0"
    )

def donation_banner():
    """Displays information about the farm's donation pledge at the bottom of the page."""
    return rx.card(
        rx.hstack(
            rx.icon("heart-handshake", size=40, color="#2d5a27"),
            rx.vstack(
                rx.heading("Our Pledge to Nature", size="5", color="#2d5a27"),
                rx.text(
                    "1% of our monthly revenue will be donated along with the excess produces "
                    'to "The natural reservation of Buffalos" from the Retezat Mountains.',
                    color="gray", size="2"
                ),
                align_items="start"
            ),
            spacing="4", align_items="center"
        ),
        width="100%", margin_top="40px", margin_bottom="40px", padding="20px", 
        background_color="#f0fdf4", border="1px solid #bbf7d0"
    )

def order_history_row(order: dict):
    """Displays a single order in the history modal."""
    # REQ-7.7: We only allow cancellation if the order is still "Created"
    is_created = (order["status"] == "Created")
    
    return rx.table.row(
        rx.table.row_header_cell(order["id"].to(str)[:6].upper() + "..."),
        rx.table.cell(order["timestamp"].to(str)),
        rx.table.cell(f"{order['total'].to(str)} RON", weight="bold"),
        rx.table.cell(
            rx.badge(
                order["status"].to(str), 
                color_scheme=rx.cond(is_created, "blue", rx.cond(order["status"] == "Cancelled", "red", "green"))
            )
        ),
        rx.table.cell(
            rx.button(
                "Cancel", 
                size="1", 
                color_scheme="red", 
                variant="soft",
                disabled=~is_created, # Disable the button if it's already cancelled or processing
                on_click=lambda: StoreState.cancel_my_order(order["id"].to(str))
            )
        ),
    )


def storefront_page():
    return rx.box(
        quantity_dialog(), # Modal component placed here
        
        
        # Bara de navigare reactivă pe care am creat-o mai sus
        navbar(),
        
        rx.vstack(

            # REQ-5.4: Farm Info Banner added right below the navbar
            rx.box(farm_info_banner(), width="80%", max_width="900px"),

            # Search Section
            rx.center(
                rx.input(
                    placeholder="Pick a vegetable",
                    on_change=StoreState.set_search_value,
                    width="600px", 
                    margin_top="40px", 
                    border="2px solid #2d5a27",
                    box_shadow="lg",
                    background_color="white",
                    size="3",
                    border_radius="full",
                ),
                width="100%",
            ),
            
            # Products Grid
            rx.cond(
                StoreState.has_results,
                rx.flex(
                    rx.foreach(StoreState.filtered_inventory, product_card), 
                    wrap="wrap", spacing="5", justify="center", padding="40px", width="100%",
                ),
                rx.vstack(
                    rx.icon("sprout", size=60, color="#ccc", margin_top="50px"),
                    rx.text("Oops, we don't grow that yet!", size="5", weight="bold", color="#666"),
                    align="center",
                ),
            ),
            
            # --- NEW: Donation Banner placed at the bottom ---
            rx.box(donation_banner(), width="80%", max_width="900px"),

            # Shopping Cart Floating Button
            rx.box(
                rx.hstack(
                    rx.icon("shopping-basket", size=25, color="white"),
                    rx.badge(StoreState.cart_count.to(str), color_scheme="orange", variant="solid", border_radius="full"), # pylint: disable=no-member
                ),
                position="fixed", bottom="40px", right="30px",
                background_color="#4caf50", padding="15px", border_radius="50px",
                box_shadow="lg", cursor="pointer",
                on_click=rx.redirect("/order"),
            ),
            width="100%", align="center",
        ),
        on_mount=StoreState.fetch_inventory,
        background_color="#f8fafc", min_height="100vh",
    )