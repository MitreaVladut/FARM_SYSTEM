"""Data Import/Export Module - Feature 10"""
import reflex as rx
import datetime
from .auth_utils import require_admin_only
from .db import export_full_database, restore_database  

class BackupState(rx.State): # pylint: disable=inherit-non-class
    """Handles the state for downloading and uploading backups."""
    
    is_uploading: bool = False

    def download_backup(self):
        """REQ-10.3, 10.5: Predetermined format and automatic naming."""
        json_data = export_full_database()
        if not json_data:
            return rx.toast.error("Failed to generate backup.")
            
        # REQ-10.5: Naming convention with current date
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        filename = f"farm_backup_{date_str}.json"
        
        return rx.download(
            data=json_data,
            filename=filename
        )

    async def handle_upload(self, files: list[rx.UploadFile]):
        """REQ-10.6: Upload local files into the system."""
        self.is_uploading = True
        yield
        
        for file in files:
            upload_data = await file.read()
            json_str = upload_data.decode("utf-8")
            
            # This triggers the validation from REQ-10.7
            success = restore_database(json_str)
            
            if success:
                self.is_uploading = False
                yield rx.toast.success("System restored successfully! Data overwritten.", duration=5000)
            else:
                self.is_uploading = False
                yield rx.toast.error("Import failed! Invalid or corrupted file.", duration=5000)

@require_admin_only
def backup_page():
    return rx.box(
        # Header
        rx.hstack(
            rx.heading("System Configuration & Backup", color="white", size="5"),
            rx.spacer(),
            rx.link("Back to Dashboard", href="/admin", color="white", size="2"),
            background_color="#dc2626", # Red header to indicate danger zone
            padding_x="30px", padding_y="15px", width="100%",
        ),
        
        rx.center(
            rx.vstack(
                rx.heading("Database Management", size="7", color="#1e293b", margin_bottom="10px"),
                rx.text("Warning: Restoring a backup will overwrite all current farm data.", color="gray", margin_bottom="30px"),
                
                # --- EXPORT SECTION ---
                rx.card(
                    rx.vstack(
                        rx.heading("Export Data (Backup)", size="5", color="#2d5a27"),
                        rx.text("Download a complete snapshot of all parcels, crops, inventory, orders, and production records.", size="2", color="gray"),
                        rx.button(
                            "💾 Download Database Backup", 
                            on_click=BackupState.download_backup, 
                            color_scheme="green", 
                            size="3",
                            width="100%",
                            margin_top="10px"
                        ),
                    ),
                    padding="30px", width="100%", max_width="600px"
                ),
                
                # --- IMPORT SECTION ---
                rx.card(
                    rx.vstack(
                        rx.heading("Import Data (Restore)", size="5", color="#dc2626"),
                        rx.text("Upload a previously saved .json backup file. This action cannot be undone.", size="2", color="gray"),
                        
                        rx.upload(
                            rx.vstack(
                                rx.button(
                                    "Select Backup File",
                                    color_scheme="gray",
                                    variant="outline",
                                ),
                                rx.text("Drag and drop or click to select", size="1", color="gray"),
                                align="center",
                            ),
                            id="backup_upload",
                            multiple=False,
                            accept={
                                "application/json": [".json"]
                            },
                            max_files=1,
                            padding="20px",
                            border="2px dashed #cbd5e1",
                            border_radius="10px",
                            width="100%",
                            margin_top="10px"
                        ),
                        
                        rx.button(
                            "⚠️ Upload and Restore System",
                            on_click=BackupState.handle_upload(rx.upload_files(upload_id="backup_upload")),
                            color_scheme="red",
                            size="3",
                            width="100%",
                            loading=BackupState.is_uploading,
                            margin_top="10px"
                        ),
                    ),
                    padding="30px", width="100%", max_width="600px", margin_top="20px"
                ),
                align="center",
                width="100%",
                padding_y="40px"
            ),
            width="100%",
        ),
        background_color="#f8fafc",
        min_height="100vh",
    )