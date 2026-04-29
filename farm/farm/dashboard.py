"""Admin Dashboard Page - Feature 1.1"""
import reflex as rx
import plotly.graph_objects as go
import re
import math
from .auth_utils import require_admin_only
from .login import LoginState
from .db import Database, get_all_staff, delete_user, create_crop, get_all_crops, create_parcel, get_all_parcels, harvest_parcel

class DashboardState(rx.State):
    # Modal Toggles
    show_add_modal: bool = False
    show_remove_modal: bool = False
    show_crop_modal: bool = False
    show_parcel_modal: bool = False

    # Staff Form Data
    emp_name: str = ""
    emp_email: str = ""
    emp_password: str = ""
    error_message: str = ""
    staff_list: list[dict] = []
    selected_staff_option: str = ""

    # Crop Form Data
    crop_name: str = ""
    crop_yield: str = ""
    crops: list[dict] = []

    # Parcel Form Data
    parcel_name: str = ""
    parcel_area: str = ""
    parcel_crop: str = ""
    parcel_date: str = ""
    parcels: list[dict] = []

    def load_dashboard_data(self):
        try:
            self.staff_list = get_all_staff()
            self.crops = get_all_crops()
            self.parcels = get_all_parcels()
            
            if self.staff_list:
                self.selected_staff_option = f"{self.staff_list[0].get('name')} ({self.staff_list[0].get('email')})"
            if self.crops:
                self.parcel_crop = self.crops[0].get("name", "")
        except Exception as e:
            print(f"Error loading dashboard data: {e}")

    # --- GEOMETRIC FARM MAP GENERATOR ---
    @rx.var
    def farm_map_figure(self) -> go.Figure:
        """Generates a proportional 2D farm layout with distinct geometric fields and fences."""
        fig = go.Figure()

        farm_width = 12.0  
        farm_height = 8.0 

        color_map = {
            "tomato": "#ef4444",   # Red
            "carrot": "#f97316",   # Orange
            "potato": "#eab308",   # Yellow
            "eggplant": "#8b5cf6", # Purple
            "lettuce": "#22c55e",  # Green
        }

        current_x = 0.5
        current_y = 0.5
        row_max_h = 0.0
        gap = 0.2  

        for p in self.parcels:
            name = p.get("name", "Parcel")
            crop = p.get("crop", "Unknown")
            date = p.get("planting_date", "Unknown")
            
            area_str = str(p.get("area", "1"))
            area_clean = re.sub(r'[^\d.-]', '', area_str)
            try:
                area_val = float(area_clean)
            except ValueError:
                area_val = 1.0

            s = math.sqrt(area_val) * 2.5

            if current_x + s > farm_width - 0.5 and current_x > 0.5:
                current_x = 0.5
                current_y += row_max_h + gap
                row_max_h = 0

            if current_y + s > farm_height - 0.5:
                farm_height = current_y + s + 2

            x_coords = [current_x, current_x+s, current_x+s, current_x, current_x]
            y_coords = [current_y, current_y, current_y+s, current_y+s, current_y]

            block_color = "#4ade80"
            for k, v in color_map.items():
                if k in crop.lower():
                    block_color = v
                    break

            hover_text = f"<b>{name}</b><br>Crop: {crop}<br>Planted: {date}<br>Area: {area_val} ha"

            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                fill="toself",
                fillcolor=block_color,
                mode="lines",
                line=dict(color="#334155", width=4), 
                text=hover_text,
                hoverinfo="text",
                name=name
            ))

            current_x += s + gap
            row_max_h = max(row_max_h, s)

        final_width = max(farm_width, current_x + 0.5)
        final_height = max(farm_height, current_y + row_max_h + 0.5)

        fig.add_shape(
            type="rect",
            x0=0, y0=0, x1=final_width, y1=final_height,
            line=dict(color="#1e293b", width=6), 
            layer="below"
        )

        if not self.parcels:
            fig.add_annotation(
                x=farm_width/2, y=farm_height/2,
                text="Farm is empty. Add a parcel!",
                showarrow=False, font=dict(size=16, color="gray")
            )

        fig.update_xaxes(visible=False, range=[-1, final_width + 1])
        fig.update_yaxes(visible=False, range=[-1, final_height + 1], scaleanchor="x", scaleratio=1)
        
        fig.update_layout(
            showlegend=False, 
            margin=dict(l=10, r=10, t=10, b=10), 
            plot_bgcolor="white",
            paper_bgcolor="#f8fafc",
            dragmode="pan" 
        )
        return fig

    # --- COMPUTED VARIABLES ---
    @rx.var
    def staff_options(self) -> list[str]:
        return [f"{s.get('name', '')} ({s.get('email', '')})" for s in self.staff_list]

    @rx.var
    def has_staff(self) -> bool:
        return len(self.staff_list) > 0

    @rx.var
    def crop_options(self) -> list[str]:
        return [c.get("name", "") for c in self.crops]

    @rx.var
    def has_crops(self) -> bool:
        return len(self.crops) > 0

    @rx.var
    def total_staff(self) -> str:
        return str(len(self.staff_list))

    @rx.var
    def total_crops(self) -> str:
        return str(len(self.crops))

    @rx.var
    def total_parcels(self) -> str:
        return str(len(self.parcels))

    @rx.var
    def has_parcels(self) -> bool:
        return len(self.parcels) > 0

    # --- MODAL OPENERS ---
    def open_add_modal(self):
        self.emp_name = ""
        self.emp_email = ""
        self.emp_password = ""
        self.error_message = ""
        self.show_add_modal = True

    def open_remove_modal(self):
        self.load_dashboard_data()
        self.show_remove_modal = True

    def open_crop_modal(self):
        self.crop_name = ""
        self.crop_yield = ""
        self.show_crop_modal = True

    def open_parcel_modal(self):
        self.parcel_name = ""
        self.parcel_area = ""
        self.parcel_date = ""
        self.load_dashboard_data()
        self.show_parcel_modal = True

    # --- STAFF ACTIONS ---
    def add_employee(self):
        if not self.emp_name or not self.emp_email or not self.emp_password:
            self.error_message = "All fields are required."
            return
        success = Database.create_user(email=self.emp_email, password=self.emp_password, name=self.emp_name, role="Staff")
        if success:
            self.show_add_modal = False
            self.load_dashboard_data()
            return rx.toast.success(f"Employee {self.emp_name} added successfully!")
        self.error_message = "Email already exists or database error."

    def remove_employee(self):
        target_id = next((s.get("id") for s in self.staff_list if f"{s.get('name')} ({s.get('email')})" == self.selected_staff_option), None)
        if target_id:
            delete_user(target_id)
            self.show_remove_modal = False
            self.load_dashboard_data()
            return rx.toast.success("Employee removed successfully!")
        return rx.toast.error("No employee selected.")

    # --- CROP & PARCEL ACTIONS ---
    def add_new_crop(self):
        if not self.crop_name or not self.crop_yield:
            return rx.toast.error("All crop fields are required.")
        success = create_crop(self.crop_name, self.crop_yield)
        if success:
            self.show_crop_modal = False
            self.load_dashboard_data()
            return rx.toast.success("Crop type added!")
        return rx.toast.error("Crop already exists.")

    def add_new_parcel(self):
        if not self.parcel_name or not self.parcel_area or not self.parcel_crop or not self.parcel_date:
            return rx.toast.error("All parcel fields are required.")
        
        success = create_parcel(
            name=self.parcel_name, 
            area=self.parcel_area, 
            crop=self.parcel_crop, 
            planting_date=self.parcel_date
        )
        
        if success:
            self.show_parcel_modal = False
            self.load_dashboard_data()
            return rx.toast.success("Parcel added successfully!")
        return rx.toast.error("Database error while adding parcel.")
    
    
    # Harvest Form Data
    show_harvest_modal: bool = False
    harvest_parcel_id: str = ""
    harvest_yield: str = ""
    harvest_notes: str = ""

    def open_harvest_modal(self, parcel_id: str):
        self.harvest_parcel_id = parcel_id
        self.harvest_yield = ""
        self.harvest_notes = ""
        self.show_harvest_modal = True

    async def confirm_harvest(self):
        if not self.harvest_yield or not self.harvest_notes:
            return rx.toast.error("Please enter the yield and notes.")
        
        # 1. Safely fetch the actual data from the other State
        login_state = await self.get_state(LoginState)
        
        # 2. Pass the real string value to the database
        success = harvest_parcel(
            parcel_id=self.harvest_parcel_id, 
            actual_yield=self.harvest_yield, 
            quality_notes=self.harvest_notes, 
            user_name=login_state.user_name 
        )
        
        if success:
            self.show_harvest_modal = False
            self.load_dashboard_data()
            return rx.toast.success("Parcel harvested and inventory updated!")
        return rx.toast.error("Database error.")

# --- UI COMPONENTS ---

def stat_card(label: str, value: str, color: str = "grass"):
    return rx.card(
        rx.vstack(
            rx.text(label, size="2", weight="medium", color="#64748b"),
            rx.text(value, size="8", weight="bold", color=color),
            align="center", spacing="1",
        ),
        width="220px", padding="20px", background_color="white", border_radius="10px", box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    )

def add_crop_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Add New Crop Type", color="#2d5a27"),
                rx.text("Define a new crop species for your farm.", size="2", color="gray"),
                rx.input(placeholder="Crop Name (e.g., Tomatoes)", on_change=DashboardState.set_crop_name, width="100%"),
                rx.input(placeholder="Expected Yield (e.g., 18 t/ha)", on_change=DashboardState.set_crop_yield, width="100%"),
                rx.hstack(
                    rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray")),
                    rx.button("Save Crop", on_click=DashboardState.add_new_crop, color_scheme="grass"),
                    spacing="3", margin_top="10px", justify="end", width="100%"
                ),
            ), max_width="400px",
        ), open=DashboardState.show_crop_modal, on_open_change=DashboardState.set_show_crop_modal,
    )

def add_parcel_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Add New Parcel", color="#2d5a27"),
                rx.text("Register a new land parcel to the database.", size="2", color="gray"),
                rx.input(placeholder="Parcel Name (e.g., North Field 1)", on_change=DashboardState.set_parcel_name, width="100%"),
                rx.input(placeholder="Area in Hectares (e.g., 4.2 ha)", on_change=DashboardState.set_parcel_area, width="100%"),
                
                rx.cond(
                    DashboardState.has_crops,
                    rx.select(
                        DashboardState.crop_options,
                        value=DashboardState.parcel_crop,
                        on_change=DashboardState.set_parcel_crop,
                        width="100%", color_scheme="grass"
                    ),
                    rx.text("Please add a Crop Type first.", color="red", size="2")
                ),
                
                rx.text("Planting Date:", size="2", color="gray", width="100%", text_align="left"),
                rx.input(type="date", on_change=DashboardState.set_parcel_date, width="100%"),
                
                rx.hstack(
                    rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray")),
                    rx.button("Save Parcel", on_click=DashboardState.add_new_parcel, color_scheme="grass", disabled=~DashboardState.has_crops),
                    spacing="3", margin_top="10px", justify="end", width="100%"
                ),
            ), max_width="400px",
        ), open=DashboardState.show_parcel_modal, on_open_change=DashboardState.set_show_parcel_modal,
    )

def parcel_row(parcel: dict):
    return rx.table.row(
        rx.table.row_header_cell(parcel["id"].to(str)[:6].upper() + "..."),
        rx.table.cell(parcel["name"].to(str)),
        rx.table.cell(parcel["area"].to(str)),
        rx.table.cell(parcel["crop"].to(str)),
        rx.table.cell(parcel["planting_date"].to(str)),
        rx.table.cell(rx.badge(parcel["status"].to(str), color_scheme="blue")),
        rx.table.cell(
            rx.cond(
                parcel["status"] != "Available",
                rx.button("Harvest", size="1", color_scheme="orange", on_click=lambda: DashboardState.open_harvest_modal(parcel["id"].to(str))),
                rx.button("Details", size="1", color_scheme="grass")
            )
        ),
    )

def add_employee_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Add New Employee", color="#2d5a27"),
                rx.cond(DashboardState.error_message != "", rx.text(DashboardState.error_message, color="red", size="2", weight="bold")),
                rx.input(placeholder="Full Name", on_change=DashboardState.set_emp_name, width="100%"),
                rx.input(placeholder="Email Address", type="email", on_change=DashboardState.set_emp_email, width="100%"),
                rx.input(placeholder="Password", type="password", on_change=DashboardState.set_emp_password, width="100%"),
                rx.hstack(
                    rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray")),
                    rx.button("Create Account", on_click=DashboardState.add_employee, color_scheme="grass"),
                    spacing="3", margin_top="10px", justify="end", width="100%"
                ),
            ), max_width="400px",
        ), open=DashboardState.show_add_modal, on_open_change=DashboardState.set_show_add_modal,
    )

def remove_employee_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Remove Employee", color="red"),
                rx.cond(
                    DashboardState.has_staff,
                    rx.select(DashboardState.staff_options, value=DashboardState.selected_staff_option, on_change=DashboardState.set_selected_staff_option, width="100%", color_scheme="red"),
                    rx.text("No active staff members found.", color="red", weight="bold")
                ),
                rx.hstack(
                    rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray")),
                    rx.button("Remove Account", on_click=DashboardState.remove_employee, color_scheme="red", disabled=~DashboardState.has_staff),
                    spacing="3", margin_top="10px", justify="end", width="100%"
                ),
            ), max_width="450px",
        ), open=DashboardState.show_remove_modal, on_open_change=DashboardState.set_show_remove_modal,
    )

def harvest_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("🚜 Harvest Parcel", color="#ea580c"),
                rx.text("Record the production cycle results.", size="2", color="gray"),
                rx.input(placeholder="Actual Yield (kg)", on_change=DashboardState.set_harvest_yield, width="100%"),
                rx.text_area(placeholder="Quality Notes (e.g., Grade A, Minor frost damage)", on_change=DashboardState.set_harvest_notes, width="100%"),
                rx.hstack(
                    rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray")),
                    rx.button("Complete Harvest", on_click=DashboardState.confirm_harvest, color_scheme="orange"),
                    spacing="3", margin_top="10px", justify="end", width="100%"
                ),
            ), max_width="400px",
        ), open=DashboardState.show_harvest_modal, on_open_change=DashboardState.set_show_harvest_modal,
    )

@require_admin_only
def dashboard_page():
    return rx.box(
        add_employee_dialog(),
        remove_employee_dialog(),
        add_crop_dialog(),
        add_parcel_dialog(),
        harvest_dialog(),

        rx.hstack(
            rx.hstack(
                rx.image(src="/Logo.ico", height="40px", width="auto", border_radius="4px"),
                rx.heading("Admin Dashboard", color="white", size="5"),
                spacing="3", align_items="center",
            ),
            rx.spacer(),
            rx.hstack(
                rx.text(f"Admin: {LoginState.user_name}", color="#deff9a", weight="bold"),
                rx.link("Back to Store", href="/", color="white", size="2"),
                rx.button("Logout", on_click=LoginState.logout, color_scheme="red", size="2"),
                spacing="4", align_items="center",
            ),
            background_color="#2d5a27", padding_x="30px", padding_y="15px", width="100%", box_shadow="0 4px 10px rgba(0,0,0,0.1)",
        ),
        
        rx.vstack(
            rx.box(width="100%", height="20px"),
            rx.heading("Overview", size="6", color="#2d5a27", width="100%", px="40px"),

            rx.hstack(
                stat_card("Total Parcels", DashboardState.total_parcels, color="#2d5a27"),
                stat_card("Crop Types", DashboardState.total_crops, color="#2d5a27"),
                stat_card("Total Staff", DashboardState.total_staff, color="#2d5a27"),
                spacing="5", padding_y="20px", justify="center", width="100%",
            ),

            rx.hstack(
                rx.button("+ New Parcel", color_scheme="blue", size="2", on_click=DashboardState.open_parcel_modal),
                rx.button("+ New Crop Type", color_scheme="blue", size="2", on_click=DashboardState.open_crop_modal),
                rx.button("Generate Report", color_scheme="green", size="2", on_click=rx.redirect("/admin/reports")),
                rx.button("+ Add Employee", color_scheme="blue", size="2", on_click=DashboardState.open_add_modal),
                rx.button("- Remove Employee", color_scheme="red", size="2", on_click=DashboardState.open_remove_modal),
                spacing="3", padding_y="10px",
            ),

            rx.vstack(
                rx.heading("My Parcels", size="4", color="#2d5a27", width="100%"),
                rx.cond(
                    DashboardState.has_parcels,
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("ID"),
                                rx.table.column_header_cell("Parcel Name"),
                                rx.table.column_header_cell("Area"),
                                rx.table.column_header_cell("Crop"),
                                rx.table.column_header_cell("Planting Date"),
                                rx.table.column_header_cell("Status"),
                                rx.table.column_header_cell("Actions"),
                                style={"background_color": "#2d5a27", "color": "white"}
                            ),
                        ),
                        rx.table.body(rx.foreach(DashboardState.parcels, parcel_row)),
                        width="100%", variant="surface", box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.1)",
                    ),
                    rx.text("No parcels registered yet. Click '+ New Parcel' to add one.", color="gray")
                ),
                width="95%", spacing="3", padding_y="20px",
            ),

            rx.vstack(
                rx.heading("Farm Layout Simulator", size="4", color="#2d5a27", width="100%"),
                rx.box(
                    rx.cond(
                        DashboardState.has_parcels,
                        rx.plotly(data=DashboardState.farm_map_figure, height="500px", width="100%"),
                        rx.center(
                            rx.text("Add a parcel to see the farm layout generate.", color="#64748b", padding="40px"),
                            width="100%", height="500px", border="2px dashed #2d5a27", border_radius="10px", background_color="#f0fdf4",
                        )
                    ),
                    width="100%",
                ), width="95%", spacing="3", padding_bottom="40px",
            ),
            align="center", width="100%",
        ),
        on_mount=DashboardState.load_dashboard_data,
        background_color="#f8fafc",
        min_height="100vh",
    )