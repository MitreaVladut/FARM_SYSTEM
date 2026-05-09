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
    edit_crop: str = "None" # NEW
    edit_date: str = ""     # NEW
    edit_status: str = ""

    # Delete Parcel Variables
    show_delete_parcel_modal: bool = False
    delete_parcel_id: str = ""
    delete_parcel_name: str = ""
    delete_parcel_status: str = ""

    # --- INTERACTIVE DRAWING GRID VARIABLES ---
    draw_mode: str = "Rectangle"
    temp_coordinates: list[dict] = []
    grid_cells: list[dict] = [] # We will build this dynamically now



 

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
        """Generates a true spatial 2D farm layout using X, Y, Width, and Height."""
        fig = go.Figure()

        # Track the outermost edges to size the map properly
        max_boundary_x = 10.0
        max_boundary_y = 10.0 

        
        color_map = {
            "tomato": "#ef4444",   
            "carrot": "#f97316",   
            "potato": "#eab308",   
            "eggplant": "#8b5cf6", 
            "lettuce": "#22c55e",  
        }

        for p in self.parcels:
            name = p.get("name", "Parcel")
            crop = p.get("crop", "Unknown")
            date = p.get("planting_date", "Unknown")
            area_str = str(p.get("area", "0"))

            # --- ADVANCED SPATIAL GEOMETRY FOR POLYGONS ---
            coords = p.get("coordinates", [])
            x_coords = []
            y_coords = []

            if coords:
                # 1. Use the new precise geometric shapes (Custom or Drawn Rectangles)
                x_coords = [float(c["x"]) for c in coords]
                y_coords = [float(c["y"]) for c in coords]
                # Append the first point to the end to close the shape!
                if len(x_coords) > 0:
                    x_coords.append(float(coords[0]["x"]))
                    y_coords.append(float(coords[0]["y"]))
                
                # Dynamic hover text for polygons
                hover_text = f"<b>{name}</b><br>Crop: {crop}<br>Planted: {date}<br>Area: {area_str} ha<br>Shape: Custom Polygon"
                
            else:
                # 2. Fallback for old rectangular legacy parcels
                try:
                    x_val = float(p.get("x", 0))
                    y_val = float(p.get("y", 0))
                    w_val = float(p.get("width", 10))
                    h_val = float(p.get("height", 10))
                except ValueError:
                    x_val, y_val, w_val, h_val = 0.0, 0.0, 10.0, 10.0

                # Must create a closed loop (5 points)
                x_coords = [x_val, x_val + w_val, x_val + w_val, x_val, x_val]
                y_coords = [y_val, y_val, y_val + h_val, y_val + h_val, y_val]
                
                # Dynamic hover text for basic rectangles
                hover_text = f"<b>{name}</b><br>Crop: {crop}<br>Planted: {date}<br>Area: {area_str}<br>Coordinates: (X: {x_val}, Y: {y_val})<br>Size: {w_val}W x {h_val}H"

            # Expand the farm grid boundary dynamically based on the largest points
            if x_coords and max(x_coords) > max_boundary_x: 
                max_boundary_x = max(x_coords)
            if y_coords and max(y_coords) > max_boundary_y: 
                max_boundary_y = max(y_coords)

            # --- COLOR MAPPING ---
            block_color = "#4ade80"
            for k, v in color_map.items():
                if k in crop.lower():
                    block_color = v
                    break

            # Update the hover text to show the exact spatial data
            hover_text = f"<b>{name}</b><br>Crop: {crop}<br>Planted: {date}<br>Area: {area_str}<br>Coordinates: (X: {x_val}, Y: {y_val})<br>Size: {w_val}W x {h_val}H"

            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                fill="toself",
                fillcolor=block_color,
                mode="lines",
                line=dict(color="#334155", width=3), 
                text=hover_text,
                hoverinfo="text",
                name=name
            ))

        # Farm Fence Boundary (Dotted line that adjusts to your largest parcel)
        fig.add_shape(
            type="rect",
            x0=-2, y0=-2, x1=max_boundary_x + 2, y1=max_boundary_y + 2,
            line=dict(color="#1e293b", width=4, dash="dot"), 
            layer="below"
        )

        fig.update_xaxes(visible=False, range=[-4, max_boundary_x + 4])
        fig.update_yaxes(visible=False, range=[-4, max_boundary_y + 4], scaleanchor="x", scaleratio=1)
        
        fig.update_layout(
            showlegend=False, 
            margin=dict(l=10, r=10, t=10, b=10), 
            plot_bgcolor="white",
            paper_bgcolor="#f8fafc",
            dragmode="pan" 
        )
        return fig
    
    def build_grid(self):
        """Builds the 40x30 grid with Y=0 at the BOTTOM and marks occupied cells."""
        from .db import is_point_in_polygon, get_polygon
        cells = []
        # Count backwards from 29 down to 0 so the top row is the highest number
        for y in range(29, -1, -1):
            for x in range(40):
                is_occupied = False
                point = {"x": float(x) + 0.49, "y": float(y) + 0.49}
                for p in self.parcels:
                    poly = get_polygon(p)
                    if is_point_in_polygon(point, poly):
                        is_occupied = True
                        break
                cells.append({"x": x, "y": y, "selected": False, "occupied": is_occupied})
        self.grid_cells = cells

    def clear_drawing(self):
        """Resets the interactive grid to 40x30."""
        self.temp_coordinates = []
        self.parcel_area = ""
        self.grid_cells = [{"x": x, "y": y, "selected": False, "occupied": False} for y in range(29, -1, -1) for x in range(40)]
        self.build_grid()

    def set_draw_mode(self, mode: str):
        self.draw_mode = mode
        self.clear_drawing()


    def handle_grid_click(self, cell: dict):
        """Handles the logic of clicking cells on the map."""
        # FIX: Remove .to(int) because the cell values are already standard integers during the event
        cx = int(cell["x"])
        cy = int(cell["y"])
        
        if self.draw_mode == "Rectangle":
            if len(self.temp_coordinates) == 0:
                # First click (Top-Left Corner)
                self.temp_coordinates = [{"x": cx, "y": cy}]
                for c in self.grid_cells:
                    c["selected"] = (c["x"] == cx) & (c["y"] == cy)
            
            elif len(self.temp_coordinates) == 1:
                # Second click (Bottom-Right Corner)
                start = self.temp_coordinates[0]
                min_x, max_x = min(start["x"], cx), max(start["x"], cx)
                min_y, max_y = min(start["y"], cy), max(start["y"], cy)
                
                # Save the 4 perfect corners for the DB
                self.temp_coordinates = [
                    {"x": min_x, "y": min_y},
                    {"x": max_x + 1, "y": min_y},
                    {"x": max_x + 1, "y": max_y + 1},
                    {"x": min_x, "y": max_y + 1}
                ]
                
                # Visually fill the rectangle with green on the grid
                for c in self.grid_cells:
                    c["selected"] = (c["x"] >= min_x) & (c["x"] <= max_x) & (c["y"] >= min_y) & (c["y"] <= max_y)
                    
                # Auto-calculate area based on grid units (e.g., each cell is 1 hectare)
                w = (max_x - min_x) + 1
                h = (max_y - min_y) + 1
                self.parcel_area = str(float(w * h))
            else:
                self.clear_drawing()
                
        elif self.draw_mode == "Polygon":
            # Custom Mode: Just drop pins
            self.temp_coordinates.append({"x": cx, "y": cy})
            
            # Reset all selected first
            for c in self.grid_cells:
                c["selected"] = False
                
            if len(self.temp_coordinates) >= 3:
                # 1. Area Calculation using Pick's Theorem
                area = 0.0
                n = len(self.temp_coordinates)
                boundary_points = 0
                for i in range(n):
                    j = (i + 1) % n
                    area += (self.temp_coordinates[i]["x"] * self.temp_coordinates[j]["y"])
                    area -= (self.temp_coordinates[j]["x"] * self.temp_coordinates[i]["y"])
                    
                    dx = abs(self.temp_coordinates[j]["x"] - self.temp_coordinates[i]["x"])
                    dy = abs(self.temp_coordinates[j]["y"] - self.temp_coordinates[i]["y"])
                    boundary_points += math.gcd(int(dx), int(dy))
                
                true_area = abs(area) / 2.0 + (boundary_points / 2.0) + 1
                self.parcel_area = str(round(true_area, 2))

                # 2. Perfect Line Drawing (Bresenham's Algorithm)
                boundary = set()
                for i in range(n):
                    x0, y0 = int(self.temp_coordinates[i]["x"]), int(self.temp_coordinates[i]["y"])
                    x1, y1 = int(self.temp_coordinates[(i+1)%n]["x"]), int(self.temp_coordinates[(i+1)%n]["y"])
                    
                    dx = abs(x1 - x0)
                    sx = 1 if x0 < x1 else -1
                    dy = -abs(y1 - y0)
                    sy = 1 if y0 < y1 else -1
                    err = dx + dy
                    while True:
                        boundary.add((x0, y0))
                        if x0 == x1 and y0 == y1:
                            break
                        e2 = 2 * err
                        if e2 >= dy:
                            err += dy
                            x0 += sx
                        if e2 <= dx:
                            err += dx
                            y0 += sy

                # 3. Fill the interior cells
                from .db import is_point_in_polygon
                for c in self.grid_cells:
                    ccx, ccy = int(c["x"]), int(c["y"])
                    if (ccx, ccy) in boundary:
                        c["selected"] = True
                    else:
                        point = {"x": float(ccx) + 0.5, "y": float(ccy) + 0.5}
                        if is_point_in_polygon(point, self.temp_coordinates):
                            c["selected"] = True
            else:
                # Highlight only the 1 or 2 pins dropped so far
                for c in self.grid_cells:
                    is_pin = any((p["x"] == c["x"] and p["y"] == c["y"]) for p in self.temp_coordinates)
                    if is_pin:
                        c["selected"] = True

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
        # Fix: Add "None" directly inside the backend state so the UI doesn't have to do the math
        options = ["None"] 
        options.extend([c.get("name", "") for c in self.crops if str(c.get("active", "true")).lower() == "true"])
        return options

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
        """REQ-8.2: Search functionality by parcel location."""
        if not self.search_query:
            return self.parcels
            
        query = self.search_query.lower().strip()
        query = "".join(e for e in query if e.isalnum() or e.isspace() or e == '.') # Allow decimals for lat/lng
        
        return [
            p for p in self.parcels 
            if query in str(p.get("name", "")).lower() 
            or query in str(p.get("status", "")).lower()
            or query in str(p.get("latitude", ""))  # REQ-8.2: Search by Latitude
            or query in str(p.get("longitude", "")) # REQ-8.2: Search by Longitude
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
        delete_parcel_dialog(),

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
                rx.button("Warehouse Logistics", color_scheme="purple", size="2", on_click=rx.redirect("/admin/inventory")),
                rx.button("+ Add Employee", color_scheme="blue", size="2", on_click=DashboardState.open_add_modal),
                rx.button("- Remove Employee", color_scheme="red", size="2", on_click=DashboardState.open_remove_modal),
                rx.button("System Backup", color_scheme="red", size="2", on_click=rx.redirect("/admin/backup")),
                spacing="3", padding_y="10px",
            ),

            rx.vstack(
                
                # 1. Added an hstack to put the search bar right next to the title
                rx.hstack(
                    rx.heading("My Parcels", size="4", color="#2d5a27"),
                    rx.spacer(),
                    rx.input(
                        placeholder="🔍 Search name, status, lat, or lng...", 
                        on_change=DashboardState.set_search_query,
                        width="300px"
                    ),
                    width="100%", align_items="center"
                ),
                
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
                        rx.table.body(rx.foreach(DashboardState.filtered_parcels, parcel_row)),
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


def interactive_drawing_grid():
    """Generates the visual drawing tool inside the modal."""
    return rx.vstack(
        rx.text("Draw Parcel Location & Geometry", size="2", color="gray", weight="bold"),
        
        # Tools
        rx.hstack(
            rx.button("⬛ Rectangle", size="1", on_click=lambda: DashboardState.set_draw_mode("Rectangle"), color_scheme=rx.cond(DashboardState.draw_mode == "Rectangle", "grass", "gray")),
            rx.button("⬡ Custom Shape", size="1", on_click=lambda: DashboardState.set_draw_mode("Polygon"), color_scheme=rx.cond(DashboardState.draw_mode == "Polygon", "blue", "gray")),
            rx.spacer(),
            rx.button("Reset Grid", size="1", on_click=DashboardState.clear_drawing, color_scheme="red", variant="ghost"),
            width="100%"
        ),
        
        # The CSS Matrix Grid
        rx.grid(
            rx.foreach(
                DashboardState.grid_cells, 
                lambda cell: rx.box(
                    width="100%", height="100%",
                    # NEW: Color it Orange if occupied, Green if selected, White if empty
                    background_color=rx.cond(
                        cell["selected"], "#4ade80", 
                        rx.cond(cell["occupied"], "#fb923c", "white")
                    ),
                    border="1px solid #e2e8f0", cursor="crosshair",
                    _hover={"background_color": "#bbf7d0"},
                    on_click=lambda: DashboardState.handle_grid_click(cell)
                )
            ),
            columns="40", width="100%", aspect_ratio="4/3", background_color="#f8fafc",
            border="2px solid #1e293b", border_radius="8px", overflow="hidden", margin_y="10px"
        ),
        
        rx.text("Calculated Area: ", rx.text.strong(DashboardState.parcel_area, " ha"), size="2", color="#2d5a27"),
        width="100%"
    )