"""Login page for Farm Management System"""
import reflex as rx
import bcrypt
from farm.db import get_user_by_email
from farm.store import StoreState

class LoginState(rx.State):  # pylint: disable=inherit-non-class
    email: str = ""
    password: str = ""
    error_message: str = ""

    async def login(self):
        """REQ-1.2: Authenticate and redirect based on role."""
        if not self.email or not self.password:
            self.error_message = "Please fill in all fields"
            return

        user = get_user_by_email(self.email)

        if user:
            stored_hash = user["password_hash"].encode('utf-8')
            # In LoginState.login (login.py)
            if bcrypt.checkpw(self.password.encode('utf-8'), stored_hash):
                store = await self.get_state(StoreState)
    
                # 1. Capture the EXACT role from the database
                user_role = user.get("role", "Customer") 
    
                # 2. Save it to the global state
                store.authenticated = True
                store.user_role = user_role 
    
                # 3. Redirect based on that specific role
                if user_role == "Admin":
                    return rx.redirect("/admin")
                elif user_role == "Staff":
                    return rx.redirect("/admin/orders") # or wherever your staff page is
                else:
                    return rx.redirect("/") # Customers go home
        
        self.error_message = "Invalid email or password"

def login_page():
    return rx.center(
        rx.vstack(
            rx.heading("Login to Farm System", color= "green", size="9"),
            rx.input(placeholder="Email", color = "white", on_change=LoginState.set_email, width="100%"),
            rx.input(placeholder="Password", color = "white", type="password", on_change=LoginState.set_password, width="100%"),
            rx.text(LoginState.error_message, color="red"),
            rx.button("Login", on_click=LoginState.login, width="100%", color_scheme="green"),
            rx.link("Back to Store", href="/", size="2"),
            # login.py (Inside the login form vstack)
            rx.link("New here? Create an account", href="/register", size="2", color="#2d5a27"),
            spacing="4",
            padding="40px",
            background="white",
            border_radius="20px",
            box_shadow="lg",
        ),
        height="100vh",
        background_color="#f8f9fa",
    )