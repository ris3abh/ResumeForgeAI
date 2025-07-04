from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import os
import json
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleDriveInput(BaseModel):
    """Input schema for Google Drive Tool."""
    operation: str = Field(..., description="Operation: 'list', 'download', 'upload', 'delete'")
    folder_type: str = Field(default="base", description="Folder type: 'base', 'generated', 'resumes', 'templates'")
    file_name: Optional[str] = Field(default=None, description="Name of the file to operate on")
    local_path: Optional[str] = Field(default=None, description="Local file path for upload/download")
    file_content: Optional[str] = Field(default=None, description="File content for direct upload")

class GoogleDriveTool(BaseTool):
    name: str = "Google Drive Tool"
    description: str = (
        "Interact with Google Drive to manage resume files, templates, and generated outputs. "
        "Can list files, download templates, upload generated resumes, and manage file operations."
    )
    args_schema: Type[BaseModel] = GoogleDriveInput

    def _run(self, operation: str, folder_type: str = "base", file_name: str = None, 
             local_path: str = None, file_content: str = None) -> str:
        """Execute Google Drive operations."""
        try:
            service = self._get_drive_service()
            folder_id = self._get_folder_id(folder_type)
            
            if not folder_id:
                return json.dumps({"status": "error", "message": f"Folder ID not found for type: {folder_type}"})
            
            if operation == "list":
                return self._list_files(service, folder_id)
            elif operation == "download":
                return self._download_file(service, folder_id, file_name, local_path)
            elif operation == "upload":
                return self._upload_file(service, folder_id, file_name, local_path, file_content)
            elif operation == "delete":
                return self._delete_file(service, folder_id, file_name)
            else:
                return json.dumps({"status": "error", "message": f"Unsupported operation: {operation}"})
                
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _get_drive_service(self):
        """Initialize Google Drive service with authentication."""
        SCOPES = ['https://www.googleapis.com/auth/drive']
        
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
        
        return build('drive', 'v3', credentials=creds)

    def _get_folder_id(self, folder_type: str) -> str:
        """Get folder ID based on folder type."""
        folder_mapping = {
            "base": os.getenv('GOOGLE_DRIVE_BASE_FOLDER'),
            "generated": os.getenv('GOOGLE_DRIVE_GENERATED_FOLDER'),
            "resumes": os.getenv('GOOGLE_DRIVE_RESUMES_FOLDER'),
            "templates": os.getenv('GOOGLE_DRIVE_TEMPLATES_FOLDER'),
            "job_descriptions": os.getenv('GOOGLE_DRIVE_JOB_DESCRIPTION_FOLDER')
        }
        return folder_mapping.get(folder_type, "")

    def _list_files(self, service, folder_id: str) -> str:
        """List files in a Google Drive folder."""
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            file_list = []
            for file in files:
                file_info = {
                    "id": file['id'],
                    "name": file['name'],
                    "type": file['mimeType'],
                    "size": file.get('size', 'N/A'),
                    "modified": file.get('modifiedTime', 'N/A')
                }
                file_list.append(file_info)
            
            return json.dumps({
                "status": "success",
                "folder_id": folder_id,
                "files": file_list,
                "count": len(file_list)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _download_file(self, service, folder_id: str, file_name: str, local_path: str) -> str:
        """Download a file from Google Drive."""
        try:
            if not file_name:
                return json.dumps({"status": "error", "message": "File name is required for download"})
            
            # Find the file
            query = f"'{folder_id}' in parents and name='{file_name}' and trashed=false"
            results = service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])
            
            if not files:
                return json.dumps({"status": "error", "message": f"File '{file_name}' not found in folder"})
            
            file_id = files[0]['id']
            
            # Download the file
            request = service.files().get_media(fileId=file_id)
            
            if local_path:
                # Download to specified local path
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'wb') as f:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                
                return json.dumps({
                    "status": "success",
                    "message": f"File downloaded to {local_path}",
                    "file_name": file_name,
                    "local_path": local_path
                })
            else:
                # Download to memory and return content
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                content = fh.getvalue()
                
                return json.dumps({
                    "status": "success",
                    "message": "File downloaded to memory",
                    "file_name": file_name,
                    "content_size": len(content),
                    "content": content.decode('utf-8', errors='ignore')[:1000]  # First 1000 chars
                })
                
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _upload_file(self, service, folder_id: str, file_name: str, local_path: str = None, file_content: str = None) -> str:
        """Upload a file to Google Drive."""
        try:
            if not file_name:
                return json.dumps({"status": "error", "message": "File name is required for upload"})
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            
            if local_path and os.path.exists(local_path):
                # Upload from local file
                media = MediaFileUpload(local_path)
                
                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                return json.dumps({
                    "status": "success",
                    "message": f"File uploaded from {local_path}",
                    "file_name": file_name,
                    "file_id": file.get('id'),
                    "folder_id": folder_id
                })
                
            elif file_content:
                # Upload from content string
                media = MediaIoBaseUpload(
                    io.BytesIO(file_content.encode('utf-8')),
                    mimetype='text/plain'
                )
                
                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                
                return json.dumps({
                    "status": "success",
                    "message": "File uploaded from content",
                    "file_name": file_name,
                    "file_id": file.get('id'),
                    "folder_id": folder_id
                })
            else:
                return json.dumps({"status": "error", "message": "Either local_path or file_content must be provided"})
                
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def _delete_file(self, service, folder_id: str, file_name: str) -> str:
        """Delete a file from Google Drive."""
        try:
            if not file_name:
                return json.dumps({"status": "error", "message": "File name is required for deletion"})
            
            # Find the file
            query = f"'{folder_id}' in parents and name='{file_name}' and trashed=false"
            results = service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])
            
            if not files:
                return json.dumps({"status": "error", "message": f"File '{file_name}' not found in folder"})
            
            file_id = files[0]['id']
            
            # Delete the file
            service.files().delete(fileId=file_id).execute()
            
            return json.dumps({
                "status": "success",
                "message": f"File '{file_name}' deleted successfully",
                "file_name": file_name,
                "file_id": file_id
            })
            
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    # Helper methods for common operations
    def get_base_resume_template(self) -> str:
        """Get the base resume template from Templates folder."""
        return self._run("list", "templates")

    def save_generated_resume(self, file_name: str, content: str) -> str:
        """Save generated resume to Generated folder."""
        return self._run("upload", "generated", file_name, file_content=content)