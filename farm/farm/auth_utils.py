import reflex as rx
from typing import Callable

def require_admin_only(page_content_func: Callable):
    """HARDLOCK: Only allows users with the 'Admin' role."""
    def protected_page():
        from .store import StoreState
        return rx.fragment(
            rx.cond(
                StoreState.authenticated & (StoreState.user_role == "Admin"),
                page_content_func(),
                rx.center(rx.vstack(rx.spinner(), rx.text("Admin Access Only..."), height="100vh")),
            ),
            on_mount=StoreState.check_admin_permissions 
        )
    return protected_page

def require_staff_or_admin(page_content_func: Callable):
    """Standard Lock: Allows both Staff and Admins."""
    def protected_page():
        from .store import StoreState
        return rx.fragment(
            rx.cond(
                StoreState.authenticated & ((StoreState.user_role == "Admin") | (StoreState.user_role == "Staff")),
                page_content_func(),
                rx.center(rx.vstack(rx.spinner(), rx.text("Verifying Credentials..."), height="100vh")),
            ),
            on_mount=StoreState.check_staff_permissions 
        )
    return protected_page