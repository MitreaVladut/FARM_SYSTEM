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
    new_soil_type: str = ""
    new_irrigation: bool = False
    crop_duration: str = ""
    crop_season: str = ""
    crop_resources: str = ""


    search_query: str = ""

    # Variables for the Expansion Modal
    show_expand_modal: bool = False
    expand_target_id: str = ""
    expand_new_width: str = ""
    expand_new_height: str = ""

    new_lat: str = ""
    new_lng: str = ""
    new_x: str = "0"
    new_y: str = "0"
    new_width: str = "10"
    new_height: str = "10"

    show_edit_modal: bool = False
    edit_parcel_id: str = ""
    edit_name: str = ""
    edit_area: str = ""
    edit_lat: str = ""
    edit_lng: str = ""
    edit_x: str = "0"
    edit_y: str = "0"
    edit_width: str = "10"
    edit_height: str = "10"
    edit_soil_type: str = ""
    edit_irrigation: bool = False
    

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
    def active_crop_options(self) -> list[str]:
        """REQ-3.7: Deactivated types no longer appear in new production planning."""
        return [c.get("name", "") for c in self.crops if str(c.get("active", "true")).lower() == "true"]

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
        # Reset coordinates when opening modal
        self.new_lat = ""
        self.new_lng = ""
        self.new_x = "0"
        self.new_y = "0"
        self.new_width = "10"
        self.new_height = "10"
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
            return rx.toast.error("Name and Yield are required.")
            
        from .db import create_crop
        success = create_crop(
            self.crop_name, 
            self.crop_yield, 
            self.crop_duration, 
            self.crop_season, 
            self.crop_resources
        )
        if success:
            self.show_crop_modal = False
            self.load_dashboard_data()
            return rx.toast.success("Crop type added!")
        return rx.toast.error("Crop already exists.")
    def add_new_parcel(self):
        if self.parcel_crop and self.parcel_crop != "None":
            if self.parcel_crop not in self.active_crop_options:
                return rx.toast.error(f"Security Error: '{self.parcel_crop}' is deactivated and cannot be planned.")
        if not self.parcel_name or not self.parcel_area or not self.parcel_crop or not self.parcel_date:
            return rx.toast.error("All parcel fields are required.")
        
        # Ensure we pass integers for the grid coordinates
        try:
            x_val = int(self.new_x) if self.new_x else 0
            y_val = int(self.new_y) if self.new_y else 0
            w_val = int(self.new_width) if self.new_width else 10
            h_val = int(self.new_height) if self.new_height else 10
        except ValueError:
            return rx.toast.error("Grid coordinates (X, Y, Width, Height) must be numbers.")

        success = create_parcel(
            name=self.parcel_name, 
            area=self.parcel_area, 
            crop=self.parcel_crop, 
            planting_date=self.parcel_date,
            lat=self.new_lat,
            lng=self.new_lng,
            x=x_val,
            y=y_val,
            w=w_val,
            h=h_val,
            soil_type=self.new_soil_type,  # NEW
            irrigation=self.new_irrigation # NEW
        )
        
        if success:
            self.show_parcel_modal = False
            self.load_dashboard_data()
            return rx.toast.success("Parcel added successfully!")
        return rx.toast.error("Database error while adding parcel.")
    def open_edit_modal(self, p_id: str, p_name: str, p_area: str, p_lat: str, p_lng: str, p_x: str, p_y: str, p_w: str, p_h: str):
        """Loads parcel data into the edit variables and opens the modal."""
        self.edit_parcel_id = str(p_id)
        self.edit_name = str(p_name)
        self.edit_area = str(p_area)
        self.edit_lat = str(p_lat) if p_lat and p_lat != "None" else ""
        self.edit_lng = str(p_lng) if p_lng and p_lng != "None" else ""
        self.edit_x = str(p_x) if p_x and p_x != "None" else "0"
        self.edit_y = str(p_y) if p_y and p_y != "None" else "0"
        self.edit_width = str(p_w) if p_w and p_w != "None" else "10"
        self.edit_height = str(p_h) if p_h and p_h != "None" else "10"
        self.show_edit_modal = True

    def save_parcel_edits(self):
        """Calls the DB function to update the parcel and coordinates."""
        if not self.edit_name or not self.edit_area:
            return rx.toast.error("Name and Area are required.")
            
        # Robust conversion: Default to 0/10 if empty, handle strings safely
        try:
            x_val = int(self.edit_x) if str(self.edit_x).strip() else 0
            y_val = int(self.edit_y) if str(self.edit_y).strip() else 0
            w_val = int(self.edit_width) if str(self.edit_width).strip() else 10
            h_val = int(self.edit_height) if str(self.edit_height).strip() else 10
        except ValueError:
            return rx.toast.error("Grid coordinates (X, Y, Width, Height) must be numbers.")

        # Ensure we are importing the correct function
        from .db import update_parcel
        
        # Call the DB update
        success = update_parcel(
            str(self.edit_parcel_id),
            str(self.edit_name),
            str(self.edit_area),
            str(self.edit_lat),
            str(self.edit_lng),
            x_val,
            y_val,
            w_val,
            h_val,
            str(self.edit_soil_type), # NEW
            self.edit_irrigation      # NEW
        )
        
        if success:
            self.show_edit_modal = False
            self.load_dashboard_data()  # Refreshes table AND map data
            return rx.toast.success(f"Parcel '{self.edit_name}' updated!")
        
        return rx.toast.error("Database error: Could not save edits.")
    
    def toggle_crop(self, crop_id: str, current_status_str: str):
        # FIX: Safely parse the text into a real Python boolean, then flip it
        is_active = (str(current_status_str) == "true")
        new_status = not is_active
        
        from .db import toggle_crop_status
        success = toggle_crop_status(crop_id, new_status)
        if success:
            self.load_dashboard_data()
            return rx.toast.success("Crop status updated!")
        return rx.toast.error("Database error.")

    def toggle_parcel(self, parcel_id: str, current_status_str: str):
        is_active = (str(current_status_str) == "true")
        new_status = not is_active
        
        from .db import toggle_parcel_status
        success = toggle_parcel_status(parcel_id, new_status)
        if success:
            self.load_dashboard_data()
            return rx.toast.success("Parcel status updated!")
        return rx.toast.error("Database error.")
    
    
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
    
    @rx.var
    def filtered_parcels(self) -> list[dict]:
        if not self.search_query:
            return self.parcels
            
        query = self.search_query.lower().strip()
        query = "".join(e for e in query if e.isalnum() or e.isspace())
        
        return [
            p for p in self.parcels 
            if query in str(p.get("name", "")).lower() or query in str(p.get("status", "")).lower()
        ]
    
    def open_expand_modal(self, parcel_id: str, current_w: int, current_h: int):
        self.expand_target_id = parcel_id
        self.expand_new_width = str(current_w)
        self.expand_new_height = str(current_h)
        self.show_expand_modal = True

    def close_expand_modal(self):
        self.show_expand_modal = False

    def confirm_expansion(self):
        # Convert inputs to integers safely
        try:
            w = int(self.expand_new_width)
            h = int(self.expand_new_height)
        except ValueError:
            return rx.toast.error("Width and height must be numbers!")

        # Call the DB function we just made
        from .db import expand_parcel # ensure this is imported
        success, message = expand_parcel(self.expand_target_id, w, h)
        
        if success:
            self.show_expand_modal = False
            self.load_parcels() # Refresh your list
            return rx.toast.success(message)
        else:
            # THIS triggers the exact red error message from your requirements
            return rx.toast.error(message)

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

def crop_list_row(crop: dict):
    """A row inside the crop manager to toggle active status."""
    is_active = (crop["active"] == "true")
    return rx.hstack(
        rx.text(crop["name"].to(str), weight="bold"),
        rx.spacer(),
        rx.badge(rx.cond(is_active, "Active", "Inactive"), color_scheme=rx.cond(is_active, "green", "red")),
        rx.button(
            rx.cond(is_active, "Deactivate", "Activate"),
            size="1", color_scheme=rx.cond(is_active, "red", "green"), variant="soft",
            on_click=lambda: DashboardState.toggle_crop(crop["id"].to(str), crop["active"].to(str))
        ),
        width="100%", align_items="center", border_bottom="1px solid #e2e8f0", padding_y="8px"
    )

def add_crop_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("🚜 Manage Crop Types", color="#2d5a27"),
                
                # --- NEW CROP CREATION ---
                rx.text("Register a New Crop:", size="2", weight="bold", color="gray"),
                rx.input(placeholder="Crop Name (e.g., Tomatoes)", on_change=DashboardState.set_crop_name, width="100%"),
                rx.input(placeholder="Expected Yield (e.g., 18 t/ha)", on_change=DashboardState.set_crop_yield, width="100%"),
                rx.input(placeholder="Growth Duration (e.g., 90 days)", on_change=DashboardState.set_crop_duration, width="100%"),
                rx.input(placeholder="Planting Season (e.g., Spring)", on_change=DashboardState.set_crop_season, width="100%"),
                rx.text_area(placeholder="Resources Required (e.g., High Water)", on_change=DashboardState.set_crop_resources, width="100%"),
                rx.button("Save New Crop", on_click=DashboardState.add_new_crop, color_scheme="grass", width="100%"),
                
                rx.divider(margin_y="15px"),
                
                # --- EXISTING CROP MANAGEMENT (REQ-3.6) ---
                rx.text("Active System Crops:", size="2", weight="bold", color="gray"),
                rx.vstack(
                    rx.foreach(DashboardState.crops, crop_list_row),
                    width="100%", max_height="200px", overflow_y="auto" # Scrollable if there are many crops
                ),
                
                rx.hstack(
                    rx.dialog.close(rx.button("Close Panel", variant="soft", color_scheme="gray")),
                    spacing="3", margin_top="10px", justify="end", width="100%"
                ),
            ), max_width="500px",
        ), open=DashboardState.show_crop_modal, on_open_change=DashboardState.set_show_crop_modal,
    )
def add_parcel_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Add New Parcel", color="#2d5a27"),
                rx.text("Register a new land parcel to the database.", size="2", color="gray"),
                
                # Basic Info
                rx.input(placeholder="Parcel Name (e.g., North Field 1)", on_change=DashboardState.set_parcel_name, width="100%"),
                rx.input(placeholder="Area in Hectares (e.g., 4.2 ha)", on_change=DashboardState.set_parcel_area, width="100%"),
                
                rx.cond(
                    DashboardState.has_crops,
                    rx.select(
                        DashboardState.active_crop_options,
                        value=DashboardState.parcel_crop,
                        on_change=DashboardState.set_parcel_crop,
                        width="100%", color_scheme="grass"
                    ),
                    rx.text("Please add a Crop Type first.", color="red", size="2")
                ),
                
                rx.text("Planting Date:", size="2", color="gray", width="100%", text_align="left"),
                rx.input(type="date", on_change=DashboardState.set_parcel_date, width="100%"),
                
                rx.divider(),
                rx.text("Location & Size Coordinates:", size="2", color="gray", width="100%", text_align="left"),
                rx.text("Environment & Soil:", size="2", color="gray", width="100%", text_align="left"),
                rx.input(placeholder="Soil Type (e.g., Clay, Sandy)", on_change=DashboardState.set_new_soil_type, width="100%"),
                rx.checkbox("Irrigation System Available", on_change=DashboardState.set_new_irrigation, color_scheme="blue", margin_bottom="10px"),

                # Geographic Coordinates
                rx.hstack(
                    rx.input(placeholder="Latitude (e.g., 44.3202)", on_change=DashboardState.set_new_lat, width="100%"),
                    rx.input(placeholder="Longitude (e.g., 23.7949)", on_change=DashboardState.set_new_lng, width="100%"),
                    width="100%"
                ),
                
                # Grid Coordinates (For Collision/Expansion)
                rx.hstack(
                    rx.input(placeholder="Grid X", on_change=DashboardState.set_new_x, width="25%"),
                    rx.input(placeholder="Grid Y", on_change=DashboardState.set_new_y, width="25%"),
                    rx.input(placeholder="Width", on_change=DashboardState.set_new_width, width="25%"),
                    rx.input(placeholder="Height", on_change=DashboardState.set_new_height, width="25%"),
                    width="100%"
                ),
                
                rx.hstack(
                    rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray")),
                    rx.button("Save Parcel", on_click=DashboardState.add_new_parcel, color_scheme="grass", disabled=~DashboardState.has_crops),
                    spacing="3", margin_top="10px", justify="end", width="100%"
                ),
            ), max_width="450px",
        ), open=DashboardState.show_parcel_modal, on_open_change=DashboardState.set_show_parcel_modal,
    )

def parcel_row(parcel: dict):
    # 1. Read the active state from the database dictionary
    is_active = (parcel["active"] == "true")
    
    return rx.table.row(
        rx.table.row_header_cell(parcel["id"].to(str)[:6].upper() + "..."),
        rx.table.cell(parcel["name"].to(str)),
        rx.table.cell(parcel["area"].to(str)),
        rx.table.cell(parcel["crop"].to(str)),
        rx.table.cell(parcel["planting_date"].to(str)),
        rx.table.cell(
            # 2. Show "Inactive" (grey) if deactivated, otherwise show normal status (blue)
            rx.badge(
                rx.cond(is_active, parcel["status"].to(str), "Inactive"), 
                color_scheme=rx.cond(is_active, "blue", "gray")
            )
        ),
        rx.table.cell(
            rx.hstack( 
                rx.cond(
                    parcel["status"] != "Available",
                    # Disable harvest if inactive
                    rx.button("Harvest", size="1", color_scheme="orange", disabled=~is_active, on_click=lambda: DashboardState.open_harvest_modal(parcel["id"].to(str))),
                ),
                # Add the Edit button
                rx.button(
                    "Edit", 
                    size="1", 
                    color_scheme="blue", 
                    variant="soft",
                    disabled=~is_active, # Disable edit if inactive
                    on_click=lambda: DashboardState.open_edit_modal(
                        parcel["id"], 
                        parcel["name"], 
                        parcel["area"],
                        parcel.get("latitude", ""),
                        parcel.get("longitude", ""),
                        parcel.get("x", "0"),
                        parcel.get("y", "0"),
                        parcel.get("width", "10"),
                        parcel.get("height", "10"),
                        parcel.get("soil_type", ""),    # Phase 1 variable
                        parcel.get("irrigation", False) # Phase 1 variable
                    )
                ),
                # 3. Add the brand new Activation Toggle Button
                rx.button(
                    rx.cond(is_active, "Deactivate", "Activate"), 
                    size="1", 
                    color_scheme=rx.cond(is_active, "red", "green"), 
                    variant="surface",
                    on_click=lambda: DashboardState.toggle_parcel(parcel["id"].to(str), parcel["active"].to(str))
                
                ),
                spacing="2"
            )
        ),
        # 4. Dim the entire row visually if deactivated
        opacity=rx.cond(is_active, "1.0", "0.5") 
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
        edit_parcel_dialog(),

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
                rx.button("System Backup", color_scheme="red", size="2", on_click=rx.redirect("/admin/backup")),
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

def edit_parcel_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Edit Parcel Details", color="#2d5a27"),
                rx.text("Update basic info and location data.", size="2", color="gray"),
                
                # Basic Info
                rx.text("Parcel Name", size="1", color="gray", width="100%", text_align="left"),
                rx.input(value=DashboardState.edit_name, on_change=DashboardState.set_edit_name, width="100%"),
                
                rx.text("Area (ha)", size="1", color="gray", width="100%", text_align="left"),
                rx.input(value=DashboardState.edit_area, on_change=DashboardState.set_edit_area, width="100%"),
                
                rx.divider(margin_y="10px"),
                rx.text("Location & Size Coordinates:", size="2", color="gray", width="100%", text_align="left"),
                rx.text("Environment & Soil:", size="2", color="gray", width="100%", text_align="left"),
                rx.input(placeholder="Soil Type", value=DashboardState.edit_soil_type, on_change=DashboardState.set_edit_soil_type, width="100%"),
                rx.checkbox("Irrigation System Available", checked=DashboardState.edit_irrigation, on_change=DashboardState.set_edit_irrigation, color_scheme="blue", margin_bottom="10px"),
                
                # Geographic Coordinates
                rx.hstack(
                    rx.vstack(
                        rx.text("Lat", size="1", color="gray"),
                        rx.input(value=DashboardState.edit_lat, on_change=DashboardState.set_edit_lat, width="100%"),
                        width="100%"
                    ),
                    rx.vstack(
                        rx.text("Lng", size="1", color="gray"),
                        rx.input(value=DashboardState.edit_lng, on_change=DashboardState.set_edit_lng, width="100%"),
                        width="100%"
                    ),
                    width="100%"
                ),
                
                # Grid Coordinates
                rx.hstack(
                    rx.vstack(
                        rx.text("X", size="1", color="gray"),
                        rx.input(value=DashboardState.edit_x, on_change=DashboardState.set_edit_x, width="100%"),
                    ),
                    rx.vstack(
                        rx.text("Y", size="1", color="gray"),
                        rx.input(value=DashboardState.edit_y, on_change=DashboardState.set_edit_y, width="100%"),
                    ),
                    rx.vstack(
                        rx.text("W", size="1", color="gray"),
                        rx.input(value=DashboardState.edit_width, on_change=DashboardState.set_edit_width, width="100%"),
                    ),
                    rx.vstack(
                        rx.text("H", size="1", color="gray"),
                        rx.input(value=DashboardState.edit_height, on_change=DashboardState.set_edit_height, width="100%"),
                    ),
                    width="100%"
                ),
                
                rx.hstack(
                    rx.dialog.close(rx.button("Cancel", variant="soft", color_scheme="gray")),
                    rx.button("Save Changes", on_click=DashboardState.save_parcel_edits, color_scheme="blue"),
                    spacing="3", margin_top="15px", justify="end", width="100%"
                ),
            ), max_width="450px",
        ), open=DashboardState.show_edit_modal, on_open_change=DashboardState.set_show_edit_modal,
    )