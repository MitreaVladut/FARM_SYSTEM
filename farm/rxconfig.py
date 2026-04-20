"""Reflex configuration for Farm Management System"""
import reflex as rx
from reflex.plugins.sitemap import SitemapPlugin # Use full path [cite: 280]

# pylint: disable=not-callable
config = rx.Config(
    app_name="farm",
    loglevel=rx.constants.LogLevel.INFO,
    disable_plugins=[SitemapPlugin], # Pass the class, not a string
)