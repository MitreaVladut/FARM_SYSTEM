"""Login Page and Authentication State Management"""
import reflex as rx
from .db import Database

class LoginState(rx.State): # pylint: disable=inherit-non-class
    """Manages the authentication session and login logic."""
    email: str = ""
    password: str = ""
    error_message: str = ""
    
    # Core session variables isolated from StoreState
    is_authenticated: bool = False
    current_user_id: str = ""
    user_role: str = ""
    user_name: str = ""

    def login(self):
        """Processes the login attempt and redirects based on role."""
        print(f"🔍 1. Încercare de logare pentru: '{self.email}'")
        self.error_message = "" 
        
        # Apelăm baza de date
        user = Database.verify_user(self.email, self.password)
        print(f"🔍 2. Răspuns de la baza de date: {user}")
        
        if user:
            print(f"✅ 3. Autentificare reușită! Rol: {user.get('role')}. Pregătesc redirectul...")
            self.is_authenticated = True
            self.current_user_id = user["_id"]
            self.user_role = user.get("role", "Customer")
            self.user_name = user.get("name", "User")
            
            self.password = "" # Curățăm parola
            
            if self.user_role == "Admin":
                print("🚀 4. Trimit user-ul la /admin")
                return rx.redirect("/admin")
            elif self.user_role == "Staff":
                print("🚀 4. Trimit user-ul la /staff")
                return rx.redirect("/staff")
            else:
                print("🚀 4. Trimit user-ul la /")
                return rx.redirect("/")
        else:
            print("❌ 3. Autentificare eșuată. User inexistent sau parolă greșită.")
            self.error_message = "Invalid email or password."
        
    def logout(self):
        """Clears the session and returns to storefront."""
        self.reset() # Clears all state variables
        return rx.redirect("/")

def login_page():
    """Renders the login user interface."""
    return rx.box(
        rx.center(
            rx.card(
                rx.vstack(
                    rx.heading("🚜 Farm Login", size="7", color="#2d5a27", margin_bottom="10px"),
                    
                    # Error Banner
                    rx.cond(
                        LoginState.error_message != "",
                        rx.callout(
                            LoginState.error_message,
                            icon="alert-triangle",
                            color_scheme="red",
                            role="alert",
                            width="100%",
                            margin_bottom="15px"
                        )
                    ),
                    
                    # Input Fields
                    rx.text("Email", weight="bold", size="2"),
                    rx.input(
                        placeholder="admin@farm.com",
                        on_change=LoginState.set_email, # pylint: disable=no-member
                        width="100%",
                        margin_bottom="15px"
                    ),
                    
                    rx.text("Password", weight="bold", size="2"),
                    rx.input(
                        type="password",
                        placeholder="••••••••",
                        on_change=LoginState.set_password, # pylint: disable=no-member
                        width="100%",
                        margin_bottom="20px"
                    ),
                    
                    # Submit Button
                    rx.button(
                        "Sign In",
                        on_click=LoginState.login, # pylint: disable=no-member
                        width="100%",
                        size="3",
                        color_scheme="grass"
                    ),
                    
                    # Navigation Links
                    rx.hstack(
                        rx.link("← Back to Store", href="/", color="gray", size="2"),
                        rx.spacer(),
                        rx.link("New here? Create an account", href="/register", size="2", color="#2d5a27"),
                        width="100%",
                        margin_top="15px"
                    ),
                    
                    width="100%",
                    align_items="start"
                ),
                width="400px",
                padding="30px",
                box_shadow="lg"
            ),
            width="100%",
            height="100vh",
            background_color="#f8fafc"
        )
    )