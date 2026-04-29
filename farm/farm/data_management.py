"""Data Import/Export Page - REQ-10.0"""
import reflex as rx
import csv
import io
from .auth_utils import require_admin_only
from .db import Database, get_all_inventory

class DataState(rx.State): # pylint: disable=inherit-non-class
    """State for handling file uploads and downloads."""
    status_message: str = ""
    is_error: bool = False

    def export_inventory(self):
        """REQ-10.2: Export inventory data to CSV."""
        self.status_message = ""
        try:
            inventory = get_all_inventory()
            
            # Creăm un fișier CSV în memorie
            output = io.StringIO()
            fieldnames = ["name", "price", "stock", "status", "image"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in inventory:
                writer.writerow({
                    "name": item.get("name", ""),
                    "price": item.get("price", ""),
                    "stock": item.get("stock", ""),
                    "status": item.get("status", ""),
                    "image": item.get("image", "")
                })
            
            # Returnăm fișierul către browser pentru descărcare
            return rx.download(
                data=output.getvalue().encode('utf-8'),
                filename="farm_inventory_export.csv"
            )
        except Exception as e:
            self.is_error = True
            self.status_message = f"Export failed: {str(e)}"

    async def handle_upload(self, files: list[rx.UploadFile]):
        """REQ-10.1: Import inventory data from uploaded CSV."""
        self.status_message = ""
        self.is_error = False
        
        if not files:
            return
            
        try:
            file = files[0]
            upload_data = await file.read()
            content = upload_data.decode('utf-8')
            
            # Citim CSV-ul din memorie
            reader = csv.DictReader(io.StringIO(content))
            db = Database.get_db()
            
            items_added = 0
            for row in reader:
                # Validare sumară a rândului
                if row.get("name") and row.get("price"):
                    db.inventory.insert_one({
                        "name": row["name"],
                        "price": row["price"],
                        "stock": row.get("stock", "0"),
                        "status": row.get("status", "In Stock"),
                        "image": row.get("image", "/placeholder.jpg")
                    })
                    items_added += 1
                    
            self.status_message = f"Successfully imported {items_added} items!"
        except Exception as e:
            self.is_error = True
            self.status_message = f"Import failed. Ensure CSV format is correct. Error: {str(e)}"

@require_admin_only
def data_management_page():
    return rx.box(
        rx.vstack(
            rx.heading("Data Management (Import/Export)", size="7", color="#2d5a27"),
            rx.divider(margin_y="20px"),
            
            rx.cond(
                DataState.status_message != "",
                rx.callout(
                    DataState.status_message,
                    color_scheme=rx.cond(DataState.is_error, "red", "green"),
                    width="100%",
                    margin_bottom="20px"
                )
            ),
            
            # Secțiunea Export
            rx.card(
                rx.vstack(
                    rx.heading("Export Inventory", size="5"),
                    rx.text("Download the current database inventory as a CSV file.", color="gray"),
                    rx.button(
                        "Download CSV",
                        icon="download",
                        on_click=DataState.export_inventory, # pylint: disable=no-member
                        color_scheme="blue"
                    ),
                    align_items="start"
                ),
                width="100%",
                padding="20px",
                margin_bottom="20px"
            ),
            
            # Secțiunea Import
            rx.card(
                rx.vstack(
                    rx.heading("Import Inventory", size="5"),
                    rx.text("Upload a CSV file to add new items. Required columns: name, price.", color="gray"),
                    
                    rx.upload(
                        rx.vstack(
                            rx.button("Select File", color_scheme="gray", variant="outline"),
                            rx.text("Drag and drop a .csv file here or click to select"),
                            align_items="center",
                        ),
                        id="csv_upload",
                        multiple=False,
                        accept={
                            "text/csv": [".csv"]
                        },
                        padding="40px",
                        border="2px dashed #e2e8f0",
                        border_radius="10px",
                        width="100%"
                    ),
                    
                    rx.button(
                        "Upload and Process",
                        on_click=DataState.handle_upload(rx.upload_files(upload_id="csv_upload")), # pylint: disable=no-member
                        color_scheme="grass",
                        margin_top="15px"
                    ),
                    align_items="start"
                ),
                width="100%",
                padding="20px"
            ),
            
            rx.link("← Back to Dashboard", href="/admin", color="gray", margin_top="20px"),
            
            width="100%",
            max_width="800px",
            margin="auto",
            padding="40px"
        ),
        background_color="#f8fafc",
        min_height="100vh"
    )