"""Staff/Employee Management Interface for Farm System - Feature 15"""
import reflex as rx
import datetime
import csv
import io
from .auth_utils import require_staff_or_admin
from .store import StoreState

# --- STATE PENTRU PROGRAM ȘI SALARII ---

class ScheduleState(rx.State):
    """Gestionează vizualizarea programului zilnic conform REQ-4.1"""
    show_schedule: bool = False
    
    @rx.var
    def current_date_str(self) -> str:
        return datetime.datetime.now().strftime("%d %B %Y")
    
    daily_tasks: list[dict] = [
        {"id": "T001", "time": "08:00", "task": "North Irrigation", "parcel": "P01", "priority": "High"},
        {"id": "T002", "time": "10:30", "task": "Tomato Packing", "parcel": "P05", "priority": "Medium"},
        {"id": "T003", "time": "13:00", "task": "Zucchini Planting", "parcel": "P12", "priority": "High"},
        {"id": "T004", "time": "15:00", "task": "Soil Nutrient Check", "parcel": "P03", "priority": "Low"},
    ]

    def toggle_schedule(self):
        self.show_schedule = not self.show_schedule

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

    def export_salary_csv(self):
        """Exportă raportul financiar în format CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Employee Name", "Role", "Hours Worked", "Hourly Rate (RON)", "Total Gross (RON)"])
        for e in self.employee_finance:
            writer.writerow([e["name"], e["role"], e["hours"], e["rate"], e["total"]])
        
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        return rx.download(
            data=output.getvalue(),
            filename=f"salary_report_{date_str}.csv"
        )

class EmployeeState(rx.State):
    """Gestionează datele angajaților și exportul conform REQ-10.5"""
    
    employees: list[dict] = [
        {"id": "E001", "name": "Popescu Ion", "role": "Field Worker", "hire_date": "15.03.2023", "status": "Active"},
        {"id": "E005", "name": "Ionescu Maria", "role": "Supervisor", "hire_date": "10.06.2024", "status": "Active"},
        {"id": "E008", "name": "Georgescu Andrei", "role": "Driver", "hire_date": "05.11.2022", "status": "On Leave"},
        {"id": "E012", "name": "Marinescu Elena", "role": "Greenhouse", "hire_date": "20.01.2025", "status": "Active"},
        {"id": "E015", "name": "Vasilescu Mihai", "role": "Seasonal", "hire_date": "01.04.2026", "status": "Inactive"},
    ]

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

def schedule_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("📅 Daily Farm Schedule", size="6", color="#2d5a27"),
                rx.text(f"Tasks for: {ScheduleState.current_date_str}", size="2", color="#666"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Time"),
                            rx.table.column_header_cell("Task"),
                            rx.table.column_header_cell("Parcel"),
                            rx.table.column_header_cell("Priority"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(ScheduleState.daily_tasks, lambda t: rx.table.row(
                            rx.table.cell(t["time"]), 
                            rx.table.cell(t["task"]), 
                            rx.table.cell(t["parcel"]),
                            rx.table.cell(rx.badge(t["priority"], color_scheme=rx.cond(t["priority"] == "High", "red", "blue")))
                        ))
                    ), width="100%", variant="surface", margin_y="20px"
                ),
                rx.dialog.close(rx.button("Close", variant="soft", color_scheme="gray")),
                align_items="end", width="100%"
            )
        ), open=ScheduleState.show_schedule, on_open_change=ScheduleState.set_show_schedule,
    )

def salary_report_dialog():
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("💰 Salary & Hours Report", size="6", color="#2d5a27"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Employee"),
                            rx.table.column_header_cell("Hours"),
                            rx.table.column_header_cell("Rate"),
                            rx.table.column_header_cell("Total Gross"),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(SalaryState.employee_finance, lambda e: rx.table.row(
                            rx.table.cell(e["name"].to(str)),
                            rx.table.cell(e["hours"].to(str) + "h"),
                            rx.table.cell(e["rate"].to(str) + " RON/h"),
                            rx.table.cell(rx.text(e["total"].to(str) + " RON", weight="bold")),
                        ))
                    ), width="100%", variant="surface", margin_y="15px"
                ),
                rx.divider(),
                rx.hstack(
                    rx.text("Total Payout:", weight="bold"), rx.spacer(),
                    rx.text(SalaryState.total_budget_needed, color="#2d5a27", size="5", weight="bold"),
                    width="100%", padding="10px"
                ),
                rx.hstack(
                    rx.button("💾 Export CSV", color_scheme="blue", variant="outline", size="2", on_click=SalaryState.export_salary_csv),
                    rx.dialog.close(rx.button("Close", variant="soft", color_scheme="gray")),
                    spacing="3"
                ), align_items="end", width="100%"
            )
        ), open=SalaryState.show_report, on_open_change=SalaryState.set_show_report,
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
        rx.table.cell(rx.button("Details", size="1", color_scheme="green"))
    )

@require_staff_or_admin
def staff_page():
    return rx.box(
        schedule_dialog(),
        salary_report_dialog(),
        
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
                stat_card("Total Employees", "14", color="#2d5a27"),
                stat_card("Active Today", "11", color="#2d5a27"),
                stat_card("On Leave / Day Off", "2", color="#2d5a27"),
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