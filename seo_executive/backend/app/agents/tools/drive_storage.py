from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from typing import List, Dict, Any, Optional
import pandas as pd
import json
from datetime import datetime
import os

class DriveStorage:
    """Google Drive and Sheets integration for report storage."""
    
    def __init__(self, credentials: Credentials):
        self.drive_service = build('drive', 'v3', credentials=credentials)
        self.sheets_service = build('sheets', 'v4', credentials=credentials)
    
    def create_folder_structure(self, client_name: str) -> Dict[str, str]:
        """
        Create folder structure for a client.
        
        Args:
            client_name: Client name
            
        Returns:
            Dictionary of folder IDs
        """
        # Main client folder
        client_folder = self._create_folder(f"SEO_Executive_{client_name}", None)
        client_id = client_folder['id']
        
        # Subfolders
        date_str = datetime.now().strftime("%Y-%m")
        date_folder = self._create_folder(date_str, client_id)
        
        subfolders = {}
        for folder_name in ["Audits", "Keywords", "Rankings", "Reports"]:
            folder = self._create_folder(folder_name, date_folder['id'])
            subfolders[folder_name.lower()] = folder['id']
        
        return {
            "client_folder_id": client_id,
            "date_folder_id": date_folder['id'],
            **subfolders
        }
    
    def _create_folder(self, name: str, parent_id: Optional[str]) -> Dict[str, str]:
        """Create a folder in Drive."""
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id] if parent_id else []
        }
        
        folder = self.drive_service.files().create(body=metadata, fields='id, name').execute()
        return folder
    
    def create_spreadsheet(
        self, 
        title: str, 
        dataframes: Dict[str, pd.DataFrame],
        folder_id: Optional[str] = None
    ) -> str:
        """
        Create a Google Sheets spreadsheet with multiple tabs.
        
        Args:
            title: Spreadsheet title
            dataframes: Dictionary of sheet_name -> DataFrame
            folder_id: Optional folder ID to place the spreadsheet
            
        Returns:
            Spreadsheet ID
        """
        # Create spreadsheet
        spreadsheet_body = {
            'properties': {
                'title': title
            },
            'sheets': []
        }
        
        spreadsheet = self.sheets_service.spreadsheets().create(
            body=spreadsheet_body,
            fields='spreadsheetId, spreadsheetUrl'
        ).execute()
        
        spreadsheet_id = spreadsheet['spreadsheetId']
        
        # Move to folder if specified
        if folder_id:
            self.drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=folder_id,
                fields='id, parents'
            ).execute()
        
        # Add data to sheets
        first_sheet = True
        for sheet_name, df in dataframes.items():
            # Sanitize sheet name
            safe_name = sheet_name[:31].replace('/', '-').replace('\\', '-')
            
            if first_sheet:
                # Rename default sheet
                self._rename_sheet(spreadsheet_id, 0, safe_name)
                first_sheet = False
            else:
                # Add new sheet
                self._add_sheet(spreadsheet_id, safe_name)
            
            # Write data
            self._write_dataframe(spreadsheet_id, safe_name, df)
        
        return spreadsheet_id
    
    def _rename_sheet(self, spreadsheet_id: str, sheet_id: int, new_name: str):
        """Rename a sheet."""
        request = {
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'title': new_name
                },
                'fields': 'title'
            }
        }
        
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [request]}
        ).execute()
    
    def _add_sheet(self, spreadsheet_id: str, sheet_name: str):
        """Add a new sheet to spreadsheet."""
        request = {
            'addSheet': {
                'properties': {
                    'title': sheet_name
                }
            }
        }
        
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': [request]}
        ).execute()
    
    def _write_dataframe(self, spreadsheet_id: str, sheet_name: str, df: pd.DataFrame):
        """Write DataFrame to sheet."""
        # Convert DataFrame to values
        values = [df.columns.tolist()] + df.values.tolist()
        
        # Convert all values to strings
        values = [[str(v) if v is not None else "" for v in row] for row in values]
        
        body = {
            'values': values
        }
        
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption='RAW',
            body=body
        ).execute()
    
    def upload_report(self, file_path: str, folder_id: str, mime_type: str = None) -> Dict[str, str]:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Path to file
            folder_id: Folder ID to upload to
            mime_type: MIME type of file
            
        Returns:
            Uploaded file info
        """
        file_name = os.path.basename(file_path)
        
        metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        if mime_type:
            media = MediaFileUpload(file_path, mimetype=mime_type)
        else:
            media = MediaFileUpload(file_path)
        
        file = self.drive_service.files().create(
            body=metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        return {
            'id': file['id'],
            'name': file['name'],
            'webViewLink': file.get('webViewLink', '')
        }
    
    def share_file(self, file_id: str, emails: List[str], role: str = 'reader') -> bool:
        """
        Share a file with specified emails.
        
        Args:
            file_id: File ID to share
            emails: List of email addresses
            role: Permission role (reader, writer, owner)
            
        Returns:
            Success status
        """
        try:
            for email in emails:
                permission = {
                    'type': 'user',
                    'role': role,
                    'emailAddress': email
                }
                
                self.drive_service.permissions().create(
                    fileId=file_id,
                    body=permission,
                    sendNotificationEmail=True
                ).execute()
            
            return True
        except Exception as e:
            print(f"Error sharing file: {e}")
            return False
    
    def create_audit_report(self, url: str, audit_data: Dict, analysis: Dict, folder_id: str = None) -> str:
        """
        Create a comprehensive audit report in Google Sheets.
        
        Args:
            url: Audited URL
            audit_data: Raw audit data
            analysis: AI analysis results
            folder_id: Optional folder ID
            
        Returns:
            Spreadsheet ID
        """
        # Create dataframes for different sections
        summary_df = pd.DataFrame([{
            'URL': url,
            'Pages Crawled': audit_data.get('pages_crawled', 0),
            'Crawl Date': audit_data.get('crawl_date', ''),
            'Critical Issues': len(audit_data.get('issues', {}).get('critical', [])),
            'Warnings': len(audit_data.get('issues', {}).get('warnings', [])),
            'Info': len(audit_data.get('issues', {}).get('info', []))
        }])
        
        issues_data = []
        for severity in ['critical', 'warnings', 'info']:
            for issue in audit_data.get('issues', {}).get(severity, []):
                issues_data.append({
                    'Severity': severity.upper(),
                    'Page': issue.get('page', ''),
                    'Issue': issue.get('issue', '')
                })
        issues_df = pd.DataFrame(issues_data) if issues_data else pd.DataFrame(columns=['Severity', 'Page', 'Issue'])
        
        # Pages data
        pages_data = []
        for page in audit_data.get('pages', []):
            if not page.get('error'):
                pages_data.append({
                    'URL': page.get('url', ''),
                    'Status': page.get('status_code', ''),
                    'Title Length': page.get('title_length', 0),
                    'Meta Desc Length': page.get('meta_description_length', 0),
                    'H1 Count': page.get('h1_count', 0),
                    'Images w/o Alt': page.get('images_without_alt_count', 0),
                    'Has Canonical': page.get('has_canonical', False),
                    'Has Schema': page.get('has_schema', False)
                })
        pages_df = pd.DataFrame(pages_data) if pages_data else pd.DataFrame()
        
        # AI Analysis
        analysis_data = []
        if isinstance(analysis, dict):
            for key, value in analysis.items():
                analysis_data.append({
                    'Category': key,
                    'Details': json.dumps(value, indent=2)[:1000]
                })
        analysis_df = pd.DataFrame(analysis_data) if analysis_data else pd.DataFrame(columns=['Category', 'Details'])
        
        dataframes = {
            'Summary': summary_df,
            'Issues': issues_df,
            'Pages': pages_df,
            'AI Analysis': analysis_df
        }
        
        title = f"SEO Audit - {url.replace('https://', '').replace('http://', '').split('/')[0]} - {datetime.now().strftime('%Y-%m-%d')}"
        
        return self.create_spreadsheet(title, dataframes, folder_id)
    
    def list_files(self, folder_id: str, query: str = None) -> List[Dict[str, Any]]:
        """
        List files in a folder.
        
        Args:
            folder_id: Folder ID to list
            query: Optional search query
            
        Returns:
            List of files
        """
        q = f"'{folder_id}' in parents and trashed=false"
        if query:
            q += f" and {query}"
        
        results = self.drive_service.files().list(
            q=q,
            pageSize=100,
            fields='files(id, name, mimeType, modifiedTime, webViewLink)'
        ).execute()
        
        return results.get('files', [])
