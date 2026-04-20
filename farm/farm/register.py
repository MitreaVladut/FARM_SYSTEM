"""Registration page for Farm Management System - REQ-6.1"""
import reflex as rx
import bcrypt
from farm.db import get_user_by_email, create_user

class RegisterState(rx.State):  # pylint: disable=inherit-non-class
    """State for customer registration."""
    name: str = ""
    email: str = ""
    password: str = ""
    confirm_password: str = ""
    error_message: str = ""

    def register(self):
        """REQ-1.2: Account creation with email and hashed password."""
        if not self.name or not self.email or not self.password:
            self.error_message = "All fields are required."
            return

        if self.password != self.confirm_password:
            self.error_message = "Passwords do not match."
            return

        # Check if user already exists
        if get_user_by_email(self.email):
            self.error_message = "An account with this email already exists."
            return

        try:
            # Hash password before storing
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(self.password.encode('utf-8'), salt)

            new_user = {
                "name": self.name,
                "email": self.email,
                "password_hash": hashed_pw.decode('utf-8'),
                "role": "Customer"  # Default role for new signups
            }
            
            create_user(new_user)
            return rx.redirect("/login")
        except Exception as e:
            self.error_message = f"Registration failed: {str(e)}"

def register_page():
    return rx.center(
        rx.vstack(
            rx.heading("Create Account", size="7", color="#2d5a27"),
            rx.text("Join our farm-to-table community", color="#666"),
            
            rx.vstack(
                rx.text("Full Name", size="2", weight="medium", width="100%"),
                rx.input(placeholder="John Doe", on_change=RegisterState.set_name, width="100%"),
                
                rx.text("Email", size="2", weight="medium", width="100%"),
                rx.input(type="email", placeholder="email@example.com", on_change=RegisterState.set_email, width="100%"),
                
                rx.text("Password", size="2", weight="medium", width="100%"),
                rx.input(type="password", placeholder="Create password", on_change=RegisterState.set_password, width="100%"),
                
                rx.text("Confirm Password", size="2", weight="medium", width="100%"),
                rx.input(type="password", placeholder="Repeat password", on_change=RegisterState.set_confirm_password, width="100%"),
                
                rx.text(RegisterState.error_message, color="red", size="2"),
                
                rx.button(
                    "Sign Up", 
                    on_click=RegisterState.register,
                    width="100%", 
                    color_scheme="green",
                    margin_top="10px"
                ),
                rx.link("Already have an account? Login", href="/login", size="2", color="#2d5a27"),
                spacing="3",
                width="100%",
            ),
            spacing="5",
            width="400px",
            padding="40px",
            border_radius="15px",
            box_shadow="lg",
            background_color="white",
        ),
        height="100vh",
        background_color="#f8f9fa",
    )