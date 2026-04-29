"""Authentication Guard - auth_utils.py"""
import reflex as rx
from farm.login import LoginState

def require_admin_only(page_func):
    """Decorator care protejează paginile strict de Admin (ex: Reports)."""
    def wrapper(*args, **kwargs):
        return rx.cond(
            LoginState.is_authenticated & (LoginState.user_role == "Admin"),
            page_func(*args, **kwargs),
            rx.center(
                rx.vstack(
                    rx.heading("🔒 Access Denied", size="8", color="red"),
                    rx.text("You do not have Administrator privileges to view this page."),
                    rx.link("← Return to Login", href="/login", color="blue"),
                    align_items="center",
                    padding="50px"
                ),
                height="100vh",
                background_color="#f8fafc"
            )
        )
    wrapper.__name__ = page_func.__name__
    return wrapper

def require_staff_or_admin(page_func):
    """Decorator care permite accesul atât Staff-ului cât și Adminului (ex: Orders)."""
    def wrapper(*args, **kwargs):
        # Permitem accesul dacă rolul este Staff SAU Admin
        is_authorized = LoginState.is_authenticated & (
            (LoginState.user_role == "Staff") | (LoginState.user_role == "Admin")
        )
        
        return rx.cond(
            is_authorized,
            page_func(*args, **kwargs),
            rx.center(
                rx.vstack(
                    rx.heading("🔒 Access Denied", size="8", color="red"),
                    rx.text("You must be logged in as Staff or Admin to view this page."),
                    rx.link("← Return to Login", href="/login", color="blue"),
                    align_items="center",
                    padding="50px"
                ),
                height="100vh",
                background_color="#f8fafc"
            )
        )
    wrapper.__name__ = page_func.__name__
    return wrapper