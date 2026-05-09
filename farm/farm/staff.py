"""Staff/Employee Management Interface for Farm System - Feature 15"""
import reflex as rx
import datetime
import csv
import io
from .auth_utils import require_staff_or_admin
from .store import StoreState
from .db import get_all_tasks, create_task, update_task_details, update_task_status, update_task_priority, delete_task

# --- STATE PENTRU PROGRAM ȘI SALARII ---

class ScheduleState(rx.State):
    """Gestionează vizualizarea programului zilnic conectat la DB"""
    show_schedule: bool = False
    daily_tasks: list[dict] = []
    
    # Variables for the Add/Edit Modal
    show_task_modal: bool = False
    edit_task_id: str = ""
    task_time: str = ""
    task_desc: str = ""
    task_parcel: str = ""
    task_priority: str = "Medium"
    
    @rx.var
    def current_date_str(self) -> str:
        return datetime.datetime.now().strftime("%d %B %Y")
    
    def load_tasks(self):
        self.daily_tasks = get_all_tasks()

    def toggle_schedule(self):
        self.show_schedule = not self.show_schedule
        if self.show_schedule:
            self.load_tasks()

    def open_new_task(self):
        self.edit_task_id = ""
        self.task_time = ""
        self.task_desc = ""
        self.task_parcel = ""
        self.task_priority = "Medium"
        self.show_task_modal = True
        
    def open_edit_task(self, t_id: str, t_time: str, t_desc: str, t_parcel: str, t_priority: str):
        self.edit_task_id = t_id
        self.task_time = t_time
        self.task_desc = t_desc
        self.task_parcel = t_parcel
        self.task_priority = t_priority
        self.show_task_modal = True

    def save_task(self):
        if not self.task_desc or not self.task_time:
            return rx.toast.error("Time and Task description are required!")
            
        if self.edit_task_id:
            update_task_details(self.edit_task_id, self.task_time, self.task_desc, self.task_parcel, self.task_priority)
            msg = "Task updated successfully!"
        else:
            create_task(self.task_time, self.task_desc, self.task_parcel, self.task_priority)
            msg = "New task created!"
            
        self.show_task_modal = False
        self.load_tasks()
        return rx.toast.success(msg)

    def change_status(self, task_id: str, new_status: str):
        update_task_status(task_id, new_status)
        self.load_tasks()

    def change_priority(self, task_id: str, new_priority: str):
        update_task_priority(task_id, new_priority)
        self.load_tasks()
        
    def delete_selected_task(self, task_id: str):
        delete_task(task_id)
        self.load_tasks()
        return rx.toast.info("Task removed.")

class SalaryState(rx.State):
    """Generarea rapoartelor de salarii și ore conform REQ-9.5"""
    show_report: bool = False
    
    employee_finance: list[dict] = [
        {"name": "Popescu Ion", "role": "Field Worker", "hours": "160", "rate": "35", "total": "5600"},
        {"name": "Ionescu Maria", "role": "Supervisor", "hours": "155", "rate": "45", "total": "6975"},
        {"name": "Georgescu Andrei", "role": "Driver", "hours": "168", "rate": "40", "total": "6720"},
        {"name": "Marinescu Elena", "role": "Greenhouse", "hours": "140", "rate": "30", "total": "4200"},
    ]

    def toggle_report(self):
        self.show_report = not self.show_report

    @rx.var
    def total_budget_needed(self) -> str:
        total = sum(int(e["total"]) for e in self.employee_finance)
        return f"{total:,.2f} RON"

    
class EmployeeState(rx.State):
    """Gestionează datele angajaților și exportul conform REQ-10.5"""
    
    employees: list[dict] = [
        {"id": "E001", "name": "Popescu Ion", "role": "Field Worker", "hire_date": "15.03.2023", "status": "Active"},
        {"id": "E005", "name": "Ionescu Maria", "role": "Supervisor", "hire_date": "10.06.2024", "status": "Active"},
        {"id": "E008", "name": "Georgescu Andrei", "role": "Driver", "hire_date": "05.11.2022", "status": "On Leave"},
        {"id": "E012", "name": "Marinescu Elena", "role": "Greenhouse", "hire_date": "20.01.2025", "status": "Active"},
        {"id": "E015", "name": "Vasilescu Mihai", "role": "Seasonal", "hire_date": "01.04.2026", "status": "Inactive"},
    ]

    # --- NEW: Variables for Details Modal ---
    selected_employee: dict = {}
    show_details_modal: bool = False

    def open_employee_details(self, emp_id: str):
        """Finds the employee by ID and opens the modal."""
        for emp in self.employees:
            if emp["id"] == emp_id:
                self.selected_employee = emp
                self.show_details_modal = True
                break
                
    def close_details_modal(self):
        self.show_details_modal = False

    def export_employee_list(self):
        """Generează și descarcă un fișier CSV cu lista angajaților."""
        output = io.StringIO()
        writer = csv.writer(output)
        # Scriem capul de tabel
        writer.writerow(["Employee ID", "Full Name", "Role", "Hire Date", "Status"])
        # Scriem datele
        for emp in self.employees:
            writer.writerow([emp["id"], emp["name"], emp["role"], emp["hire_date"], emp["status"]])
        
        # Numele fișierului primește data curentă automat
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        return rx.download(
            data=output.getvalue(),
            filename=f"employee_list_{date_str}.csv"
        )

# --- COMPONENTE UI (DIALOGURI) ---




def employee_details_dialog():
    """The pop-up window showing employee profile details."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("👤 Employee Profile", size="6", color="#2d5a27"),
                rx.hstack(
                    rx.icon("user-circle", size=60, color="#64748b"),
                    rx.vstack(
                        rx.heading(EmployeeState.selected_employee["name"].to(str), size="5"),
                        rx.text(f"ID: {EmployeeState.selected_employee['id'].to(str)}", color="gray"),
                        align_items="start", spacing="1"
                    ),
                    spacing="4", align_items="center", padding_bottom="15px"
                ),
                rx.divider(),
                rx.text(rx.text.strong("Role: "), EmployeeState.selected_employee["role"].to(str)),
                rx.text(rx.text.strong("Hire Date: "), EmployeeState.selected_employee["hire_date"].to(str)),
                rx.text(rx.text.strong("Current Status: "), 
                    rx.badge(EmployeeState.selected_employee["status"].to(str), 
                             color_scheme=rx.cond(EmployeeState.selected_employee["status"] == "Active", "green", "gray"))
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.dialog.close(rx.button("Close Window", variant="soft", color_scheme="gray")),
                    margin_top="20px", width="100%"
                ),
                align_items="start", width="100%"
            ), max_width="400px"
        ), open=EmployeeState.show_details_modal, on_open_change=EmployeeState.set_show_details_modal,
    )
# --- PAGINA PRINCIPALĂ ---

def stat_card(label: str, value: str, color: str = "grass"):
    return rx.card(
        rx.vstack(
            rx.text(label, size="2", weight="medium", color="#666"),
            rx.text(value, size="8", weight="bold", color=color),
            align="center", spacing="1",
        ), width="220px", padding="20px", style={"background_color": "white", "border_radius": "10px"}
    )

def employee_row(emp: dict):
    """Componentă separată pentru a genera rândurile tabelului de angajați dinamic."""
    return rx.table.row(
        rx.table.cell(emp["id"], color="black"), 
        rx.table.cell(emp["name"], color="black"), 
        rx.table.cell(emp["role"], color="black"),
        rx.table.cell(emp["hire_date"], color="black"), 
        rx.table.cell(
            emp["status"], 
            color=rx.cond(emp["status"] == "Active", "green", rx.cond(emp["status"] == "Inactive", "red", "blue")), 
            weight="bold"
        ),
        rx.table.cell(
            rx.button(
                "Details", 
                size="1", 
                color_scheme="green",
                on_click=lambda: EmployeeState.open_employee_details(emp["id"].to(str))
            )
        )
    )

@require_staff_or_admin
def staff_page():
    return rx.box(
        schedule_dialog(),
        salary_report_dialog(),
        task_form_dialog(),
        employee_details_dialog(),
        
        # Header
        rx.hstack(
            rx.heading("Farm Admin Panel", color="white", size="5"),
            rx.spacer(),
            rx.hstack(
                rx.link("Back to Dashboard", href="/admin", color="white", size="2"),
                rx.link("Home", href="/", color="white", size="2"),
                rx.button("Logout", on_click=StoreState.logout, variant="ghost", color="white", size="2"),
                spacing="4",
            ),
            background_color="#2d5a27", padding_x="20px", padding_y="12px", width="100%",
        ),

        rx.vstack(
            rx.box(width="100%", height="20px"),
            rx.heading("Employee Management / Farm Team", size="6", color="#2d5a27", width="100%", px="40px"),

            # Stats Row
            rx.hstack(
                stat_card("Total Employees", "5", color="#2d5a27"),
                stat_card("Active Today", "3", color="#2d5a27"),
                stat_card("On Leave / Day Off", "1", color="#2d5a27"),
                stat_card("Hours Worked This Month", "~1,820", color="#2d5a27"),
                spacing="5", padding_y="20px", justify="center", width="100%",
            ),

            # Action Buttons - ACUM CONECTATE LA STATE
            rx.hstack(
                rx.button("Generate Salary/Hours Report", color_scheme="blue", size="2", on_click=SalaryState.toggle_report),
                rx.button("View Daily Schedule", color_scheme="blue", size="2", on_click=ScheduleState.toggle_schedule),
                rx.button("Process Orders", color_scheme="green", size="2", on_click=rx.redirect("/orders")),
                # BUTONUL DE EXPORT ACTUALIZAT:
                rx.button("Export Employee List", color_scheme="blue", size="2", on_click=EmployeeState.export_employee_list),
                spacing="3", padding_y="10px",
            ),

            # Tabelul de angajați - Acum se randează dinamic din baza de date / state
            rx.vstack(
                rx.heading("Employee List", size="4", color="#2d5a27", width="100%"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("ID", color="black"), 
                            rx.table.column_header_cell("Full Name", color="black"),
                            rx.table.column_header_cell("Role", color="black"), 
                            rx.table.column_header_cell("Hire Date", color="black"),
                            rx.table.column_header_cell("Status", color="black"), 
                            rx.table.column_header_cell("Actions", color="black"),
                            style={"background_color": "#2d5a27", "color": "white"}
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(EmployeeState.employees, employee_row)
                    ), width="100%", variant="surface",
                ), width="95%", spacing="3", padding_y="20px",
            ), align="center", width="100%",
        ),
        # Footer
        rx.center(
            rx.text("© 2026 Farm Management System • Employee Module • " + ScheduleState.current_date_str, color="#666", size="2", padding="20px"),
            width="100%", border_top="1px solid #e2e8f0", margin_top="40px",
        ),
        background_color="#f8fafc", min_height="100vh",
    )