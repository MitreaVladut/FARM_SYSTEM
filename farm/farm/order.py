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

    
