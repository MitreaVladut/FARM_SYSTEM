"""Main entry point for Farm Management System"""
import reflex as rx
from farm.login import login_page
from farm.dashboard import dashboard_page
from farm.staff import staff_page
from farm.store import storefront_page
from farm.register import register_page # Add this import
from .inventory_admin import inventory_admin_page
from farm.order import order_page
from .staff_orders import staff_orders_page
# pylint: disable=not-callable
app = rx.App(
    theme=rx.theme(
        accent_color="grass",
        radius="medium",
    )
)

# REQ: Storefront is now the landing page
app.add_page(storefront_page, route="/") 
app.add_page(login_page, route="/login")
app.add_page(dashboard_page, route="/admin")
app.add_page(staff_page, route="/staff")
app.add_page(register_page, route="/register")
app.add_page(order_page, route="/order")
app.add_page(inventory_admin_page, route="/admin/inventory")
app.add_page(staff_orders_page, route="/admin/orders")
