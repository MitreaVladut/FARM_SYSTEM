import reflex as rx
from .auth_utils import require_admin_only
from .store import StoreState
def stat_card(label: str, value: str, color: str = "grass"):
    """Helper for the top 4 metric cards."""
    return rx.card(
        rx.vstack(
            rx.text(label, size="2", weight="medium", color="#666"),
            rx.text(value, size="8", weight="bold", color=color),
            align="center",
            spacing="1",
        ),
        width="220px",
        padding="20px",
        style={"background_color": "white", "border_radius": "10px"}
    )

def action_button(text: str, color_scheme: str):
    """Helper for the colorful action bar buttons."""
    return rx.button(
        text,
        color_scheme=color_scheme,
        size="2",
        variant="solid",
        px="4",
    )
@require_admin_only
def dashboard_page():
    return rx.box(
        # 1. Dark Green Header (REQ-1.1)
        rx.hstack(
            rx.heading("Admin Dashboard", color="white", size="5"),
            rx.spacer(),
            rx.hstack(
                rx.link("Back to Home", href="/", color="white", size="2"),
                rx.button("Logout", on_click=StoreState.logout, variant="ghost", color="white", size="2"),
                spacing="4",
            ),
            background_color="#2d5a27",  # Forest Green
            padding_x="20px",
            padding_y="12px",
            width="100%",
        ),

        rx.vstack(
            rx.box(width="100%", height="20px"), # Top spacer

            # 2. Welcome Message
            rx.heading("Welcome, Administrator!", size="6", color="#2d5a27", width="100%", px="40px"),

            # 3. Stats Row
            rx.hstack(
                stat_card("Total Area", "42 ha", color="#2d5a27"),
                stat_card("Active Parcels", "18", color="#2d5a27"),
                stat_card("Estimated Production 2026", "~185 t", color="#2d5a27"),
                stat_card("New Orders", "7", color="#2d5a27"),
                spacing="5",
                padding_y="20px",
                justify="center",
                width="100%",
            ),

            # 4. Action Buttons Bar
            rx.hstack(
                action_button("+ New Parcel", "blue"),
                action_button("+ New Crop Type", "blue"),
                action_button("Generate Report", "green"),
                action_button("+ Add Employee", "blue"),
                action_button("- Remove Employee", "red"),
                spacing="3",
                padding_y="10px",
            ),

            # 5. My Parcels Section
            rx.vstack(
                rx.heading("My Parcels", size="4", color="#2d5a27", width="100%"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("ID"),
                            rx.table.column_header_cell("Parcel Name"),
                            rx.table.column_header_cell("Area"),
                            rx.table.column_header_cell("Crop"),
                            rx.table.column_header_cell("Planting Date"),
                            rx.table.column_header_cell("Status"),
                            rx.table.column_header_cell("Estimated Yield"),
                            rx.table.column_header_cell("Actions"),
                            style={"background_color": "#2d5a27", "color": "white"}
                        ),
                    ),
                    rx.table.body(
                        rx.table.row(
                            # Body cells with black text
                            rx.table.row_header_cell("P01", color="black"),
                            rx.table.cell("North Parcel 1", color="black"),
                            rx.table.cell("4.2 ha", color="black"),
                            rx.table.cell("Tomatoes", color="black"),
                            rx.table.cell("March 15, 2026", color="black"),
                            rx.table.cell("In Production", color="green"),
                            rx.table.cell("~18 t", color="black"),
                            rx.table.cell(rx.button("Details", size="1", color_scheme="green")),
                        ),
                        rx.table.row(
                            rx.table.row_header_cell("P05", color="black"),
                            rx.table.cell("East Parcel 2", color="black"),
                            rx.table.cell("3.8 ha", color="black"),
                            rx.table.cell("Carrots", color="black"),
                            rx.table.cell("April 20, 2026", color="black"),
                            rx.table.cell("Planned", color="blue"),
                            rx.table.cell("~12 t", color="black"),
                            rx.table.cell(rx.button("Details", size="1", color_scheme="green")),
                        ),
                        rx.table.row(
                            rx.table.row_header_cell("P12", color="black"),
                            rx.table.cell("South Parcel",color="black"),
                            rx.table.cell("6.5 ha", color="black"),
                            rx.table.cell("New Potatoes", color="black"),
                            rx.table.cell("February 10, 2026", color="black"),
                            rx.table.cell("Harvested", color="red"),
                            rx.table.cell("22.4 t", color="black"),
                            rx.table.cell(rx.button("Details", size="1", color_scheme="green")),
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                width="95%",
                spacing="3",
                padding_y="20px",
            ),

            # 6. Map Placeholder
            rx.vstack(
                rx.heading("Parcel Map (Location View)", size="4", color="#2d5a27", width="100%"),
                rx.box(
                    rx.center(
                        rx.text("[Interactive map with parcels will be integrated here – e.g. Leaflet / Google Maps / OpenStreetMap]", 
                                color="#666", text_align="center", padding="40px"),
                        width="100%",
                        height="300px",
                        border="1px dashed #2d5a27",
                        border_radius="10px",
                        background_color="#f0fdf4", # Very light green
                    ),
                    width="100%",
                ),
                width="95%",
                spacing="3",
                padding_bottom="40px",
            ),
            align="center",
            width="100%",
        ),
        background_color="#f8fafc",  # Light gray background
        min_height="100vh",
    )