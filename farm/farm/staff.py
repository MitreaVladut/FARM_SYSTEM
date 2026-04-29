"""Staff/Employee Management Interface for Farm System - Feature 15"""
import reflex as rx
from .auth_utils import require_staff_or_admin
from .store import StoreState
def stat_card(label: str, value: str, color: str = "grass"):
    """Helper for the top 4 employee metric cards."""
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

def action_button(text: str):
    """Helper for the simple dark blue action buttons bar."""
    return rx.button(
        text,
        color_scheme="slate",
        size="2",
        variant="solid",
        px="4",
    )
@require_staff_or_admin
def staff_page():
    return rx.box(
        # 1. Dark Green Header (Matched to Screenshot)
        rx.hstack(
            rx.heading("Farm Admin Panel", color="white", size="5"),
            rx.spacer(),
            rx.hstack(
                rx.link("Back to Dashboard", href="/admin", color="white", size="2"),
                rx.link("Home", href="/", color="white", size="2"),
                rx.button("Logout", on_click=StoreState.logout, variant="ghost", color="white", size="2"),
                spacing="4",
            ),
            background_color="#2d5a27", # Forest Green
            padding_x="20px",
            padding_y="12px",
            width="100%",
        ),

        rx.vstack(
            rx.box(width="100%", height="20px"), # Top spacer

            # 2. Main Title (Employee Management)
            rx.heading("Employee Management / Farm Team", size="6", color="#2d5a27", width="100%", px="40px"),

            # 3. Stats Row (Matched Metrics)
            rx.hstack(
                stat_card("Total Employees", "14", color="#2d5a27"),
                stat_card("Active Today", "11", color="#2d5a27"),
                stat_card("On Leave / Day Off", "2", color="#2d5a27"),
                stat_card("Hours Worked This Month", "~1,820", color="#2d5a27"),
                spacing="5",
                padding_y="20px",
                justify="center",
                width="100%",
            ),

            # 4. Colorful Action Bar Buttons (Matched Colors)
            rx.hstack(
                rx.button("Generate Salary/Hours Report", color_scheme="blue", size="2"),
                rx.button("View Daily Schedule", color_scheme="blue", size="2"),
                rx.button("Process Orders", on_click=rx.redirect("/orders"), color_scheme="green", size="2"),
                rx.button("Export Employee List", color_scheme="blue", size="2"),
                spacing="3",
                padding_y="10px",
            ),

            # 5. Employee List Section
            rx.vstack(
                rx.heading("Employee List", size="4", color="#2d5a27", width="100%"),
                
                # The stylized Table matching the reference
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("ID", color="black"),
                            rx.table.column_header_cell("Full Name", color="black"),
                            rx.table.column_header_cell("Role / Position", color="black"),
                            rx.table.column_header_cell("Phone", color="black"),
                            rx.table.column_header_cell("Email", color="black"),
                            rx.table.column_header_cell("Hire Date", color="black"),
                            rx.table.column_header_cell("Status", color="black"),
                            rx.table.column_header_cell("Last Activity", color="black"),
                            rx.table.column_header_cell("Actions", color="black"),
                            style={"background_color": "#2d5a27", "color": "white"}
                        ),
                    ),
                    rx.table.body(
                        # Row 1: Active
                        rx.table.row(
                            rx.table.row_header_cell("E001", color="black"),
                            rx.table.cell("Popescu Ion", color="black"),
                            rx.table.cell("Field Main Worker", color="black"),
                            rx.table.cell("0722 345 678", color="black"),
                            rx.table.cell("ion.popescu@farm.ro", color="black"),
                            rx.table.cell("15.03.2023", color="black"),
                            rx.table.cell("Active", color="green"),
                            rx.table.cell("Today, 08:45 – North Irrigation", color="black"),
                            rx.table.cell(
                                rx.vstack(
                                    rx.button("Details", size="1", color_scheme="green", width="100%"),
                                    rx.button("Deactivate", size="1", color_scheme="red", width="100%"),
                                    spacing="1",
                                )
                            ),
                        ),
                        # Row 2: Active
                        rx.table.row(
                            rx.table.row_header_cell("E005", color="black"),
                            rx.table.cell("Ionescu Maria", color="black"),
                            rx.table.cell("Harvest Supervisor", color="black"),
                            rx.table.cell("0741 987 654", color="black"),
                            rx.table.cell("maria.ionescu@farm.ro", color="black"),
                            rx.table.cell("10.06.2024", color="black"),
                            rx.table.cell("Active", color="green"),
                            rx.table.cell("Yesterday, 16:30 – Tomato Packing", color="black"),
                            rx.table.cell(
                                rx.vstack(
                                    rx.button("Details", size="1", color_scheme="green", width="100%"),
                                    rx.button("Deactivate", size="1", color_scheme="red", width="100%"),
                                    spacing="1",
                                )
                            ),
                        ),
                        # Row 3: On Leave
                        rx.table.row(
                            rx.table.row_header_cell("E008", color="black"),
                            rx.table.cell("Georgescu Andrei", color="black"),
                            rx.table.cell("Driver / Logistics", color="black"),
                            rx.table.cell("0765 432 109", color="black"),
                            rx.table.cell("andrei.georgescu@farm.ro", color="black"),
                            rx.table.cell("05.11.2022", color="black"),
                            rx.table.cell("On Leave", color="blue"),
                            rx.table.cell("–", color="black"),
                            rx.table.cell(
                                rx.vstack(
                                    rx.button("Details", size="1", color_scheme="green", width="100%"),
                                    rx.button("View Leave", size="1", color_scheme="blue", width="100%"),
                                    spacing="1",
                                )
                            ),
                        ),
                        # Row 4: Active
                        rx.table.row(
                            rx.table.row_header_cell("E012", color="black"),
                            rx.table.cell("Marinescu Elena", color="black"),
                            rx.table.cell("Greenhouse Worker", color="black"),
                            rx.table.cell("0733 111 222", color="black"),
                            rx.table.cell("elena.marinescu@farm.ro", color="black"),
                            rx.table.cell("20.01.2025", color="black"),
                            rx.table.cell("Active", color="green"),
                            rx.table.cell("Today, 07:30 – Zucchini Planting", color="black"),
                            rx.table.cell(
                                rx.vstack(
                                    rx.button("Details", size="1", color_scheme="green", width="100%"),
                                    rx.button("Deactivate", size="1", color_scheme="red", width="100%"),
                                    spacing="1",
                                )
                            ),
                        ),
                        # Row 5: Inactive (season ended)
                        rx.table.row(
                            rx.table.row_header_cell("E015", color="black"),
                            rx.table.cell("Vasilescu Mihai", color="black"),
                            rx.table.cell("Seasonal Worker", color="black"),
                            rx.table.cell("0721 999 888", color="black"),
                            rx.table.cell("mihai.vasilescu@farm.ro", color="black"),
                            rx.table.cell("01.04.2026", color="black"),
                            rx.table.cell(
                                rx.text("Inactive (season ended)", color="red"),
                            ),
                            rx.table.cell("–", color="black"),
                            rx.table.cell(
                                rx.vstack(
                                    rx.button("Details", size="1", color_scheme="green", width="100%"),
                                    spacing="1",
                                )
                            ),
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                width="95%",
                spacing="3",
                padding_y="20px",
            ),
            align="center",
            width="100%",
        ),
        # 6. Footer (Requirement-15.8)
        rx.center(
            rx.text("© 2026 Farm Management System • Employee Module • Current date: February 26, 2026", color="#666", size="2", padding="20px"),
            width="100%",
            border_top="1px solid #e2e8f0",
            margin_top="40px",
        ),
        background_color="#f8fafc",  # Light gray background
        min_height="100vh",
    )