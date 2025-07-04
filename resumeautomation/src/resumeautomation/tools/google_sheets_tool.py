from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleSheetsInput(BaseModel):
    """Input schema for Google Sheets Tool."""
    operation: str = Field(..., description="Operation: 'read', 'write', 'update'")
    range_name: str = Field(default="A:Z", description="Range to read/write (e.g., 'A1:G10')")
    values: Optional[list] = Field(default=None, description="Values to write (for write operations)")
    row_number: Optional[int] = Field(default=None, description="Specific row number to update")

class GoogleSheetsTool(BaseTool):
    name: str = "Google Sheets Tool"
    description: str = (
        "Interact with Google Sheets to read resume requests, update status, and manage data. "
        "Can read new requests, update status columns, and write results back to sheets."
    )
    args_schema: Type[BaseModel] = GoogleSheetsInput

    def _run(self, operation: str, range_name: str = "A:Z", values: list = None, row_number: int = None) -> str:
        """Execute Google Sheets operations."""
        try:
            service = self._get_sheets_service()
            spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
            
            if not spreadsheet_id:
                return "Error: GOOGLE_SHEETS_ID not found in environment variables"
            
            if operation == "read":
                return self._read_sheet(service, spreadsheet_id, range_name)
            elif operation == "write":
                return self._write_sheet(service, spreadsheet_id, range_name, values)
            elif operation == "update":
                return self._update_row(service, spreadsheet_id, row_number, values)
            else:
                return f"Error: Unsupported operation '{operation}'. Use 'read', 'write', or 'update'."
                
        except Exception as e:
            return f"Google Sheets error: {str(e)}"

    def _get_sheets_service(self):
        """Initialize Google Sheets service with authentication."""
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        
        creds = None
        token_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'credentials', 'token.json')
        credentials_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'credentials', 'credentials.json')
        
        # Load existing token
        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_file):
                    raise Exception(f"Credentials file not found at {credentials_file}")
                
                flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
        
        return build('sheets', 'v4', credentials=creds)

    def _read_sheet(self, service, spreadsheet_id: str, range_name: str) -> str:
        """Read data from Google Sheets."""
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, 
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return json.dumps({"status": "success", "message": "No data found", "data": []})
            
            # Process the data
            headers = values[0] if values else []
            rows = values[1:] if len(values) > 1 else []
            
            processed_data = []
            for i, row in enumerate(rows, start=2):  # Start from row 2 (after header)
                row_data = {"row_number": i}
                for j, header in enumerate(headers):
                    if j < len(row):
                        row_data[header.strip()] = row[j].strip() if row[j] else ""
                    else:
                        row_data[header.strip()] = ""
                processed_data.append(row_data)
            
            return json.dumps({
                "status": "success",
                "headers": headers,
                "data": processed_data,
                "total_rows": len(processed_data)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _write_sheet(self, service, spreadsheet_id: str, range_name: str, values: list) -> str:
        """Write data to Google Sheets."""
        try:
            if not values:
                return json.dumps({"status": "error", "message": "No values provided to write"})
            
            body = {'values': values}
            
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            
            return json.dumps({
                "status": "success",
                "message": f"Successfully updated {updated_cells} cells",
                "range": range_name
            })
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _update_row(self, service, spreadsheet_id: str, row_number: int, values: list) -> str:
        """Update a specific row in Google Sheets."""
        try:
            if not row_number or not values:
                return json.dumps({"status": "error", "message": "Row number and values are required"})
            
            # Construct range for the specific row
            range_name = f"A{row_number}:Z{row_number}"
            
            body = {'values': [values]}
            
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            
            return json.dumps({
                "status": "success",
                "message": f"Successfully updated row {row_number} with {updated_cells} cells",
                "row_number": row_number
            })
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def find_new_requests(self) -> str:
        """Helper method to find rows with 'new' or empty status."""
        try:
            result = self._run("read", "A:Z")
            data = json.loads(result)
            
            if data["status"] != "success":
                return result
            
            new_requests = []
            for row in data["data"]:
                status = row.get("Status", "").lower().strip()
                if status in ["", "new", "pending"]:
                    new_requests.append(row)
            
            return json.dumps({
                "status": "success",
                "new_requests": new_requests,
                "count": len(new_requests)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def update_status(self, row_number: int, status: str) -> str:
        """Helper method to update status of a specific row."""
        try:
            # First read the current row to preserve other data
            current_data = self._run("read", f"A{row_number}:Z{row_number}")
            data = json.loads(current_data)
            
            if data["status"] != "success" or not data["data"]:
                return json.dumps({"status": "error", "message": f"Could not read row {row_number}"})
            
            # Update the status column (assuming Status is in column E, index 4)
            row_data = list(data["data"][0].values())[1:]  # Skip row_number
            if len(row_data) >= 5:
                row_data[4] = status  # Update status column
            else:
                # Extend the row to include status
                while len(row_data) < 5:
                    row_data.append("")
                row_data[4] = status
            
            return self._update_row(None, None, row_number, row_data)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})