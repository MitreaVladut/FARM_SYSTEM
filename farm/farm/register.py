"""Registration Page"""
import reflex as rx
from .db import Database

class RegisterState(rx.State): # pylint: disable=inherit-non-class
    name: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""
    error_message: str = ""

    def register(self):
        """Validează inputurile și creează contul."""
        self.error_message = ""
        
        # Validări de bază
        if not self.name or not self.email or not self.password:
            self.error_message = "Please fill in all fields."
            return
        
        if self.password != self.confirm_password:
            self.error_message = "Passwords do not match."
            return
            
        # Încercăm să creăm contul în DB (rolul implicit va fi "Customer")
        success = Database.create_user(self.email, self.password, self.name)
        
        if success:
            # Curățăm câmpurile și trimitem utilizatorul la login
            self.name = ""
            self.email = ""
            self.password = ""
            self.confirm_password = ""
            return rx.redirect("/login")
        else:
            self.error_message = "An account with this email already exists."

def register_page():
    return rx.box(
        rx.center(
            rx.card(
                rx.vstack(
                    rx.heading("🚜 Create Account", size="7", color="#2d5a27", margin_bottom="10px"),
                    
                    # Banner pentru erori
                    rx.cond(
                        RegisterState.error_message != "",
                        rx.callout(
                            RegisterState.error_message,
                            icon="alert-triangle",
                            color_scheme="red",
                            role="alert",
                            width="100%",
                            margin_bottom="15px"
                        )
                    ),
                    
                    rx.text("Full Name", weight="bold", size="2"),
                    rx.input(
                        placeholder="Popescu Ion",
                        on_change=RegisterState.set_name, # pylint: disable=no-member
                        width="100%",
                        margin_bottom="10px"
                    ),
                    
                    rx.text("Email", weight="bold", size="2"),
                    rx.input(
                        placeholder="client@farm.ro",
                        on_change=RegisterState.set_email, # pylint: disable=no-member
                        width="100%",
                        margin_bottom="10px"
                    ),
                    
                    rx.text("Password", weight="bold", size="2"),
                    rx.input(
                        type="password",
                        placeholder="••••••••",
                        on_change=RegisterState.set_password, # pylint: disable=no-member
                        width="100%",
                        margin_bottom="10px"
                    ),
                    
                    rx.text("Confirm Password", weight="bold", size="2"),
                    rx.input(
                        type="password",
                        placeholder="••••••••",
                        on_change=RegisterState.set_confirm_password, # pylint: disable=no-member
                        width="100%",
                        margin_bottom="20px"
                    ),
                    
                    rx.button(
                        "Register",
                        on_click=RegisterState.register, # pylint: disable=no-member
                        width="100%",
                        size="3",
                        color_scheme="grass"
                    ),
                    
                    rx.link("Already have an account? Sign In", href="/login", color="#2d5a27", margin_top="15px", size="2"),
                    
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