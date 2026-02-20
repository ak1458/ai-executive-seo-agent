import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
from typing import Optional, Dict

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/webmasters.readonly',  # GSC
    'https://www.googleapis.com/auth/indexing',              # Indexing API
    'https://www.googleapis.com/auth/drive',                 # Drive
    'https://www.googleapis.com/auth/spreadsheets',          # Sheets
]

class GoogleAuthService:
    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")
        self.token_file = "data/token.json"
    
    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=SCOPES,
            redirect_uri=self.redirect_uri
        )
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        return auth_url
    
    def exchange_code(self, code: str) -> Dict:
        """Exchange authorization code for tokens."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=SCOPES,
            redirect_uri=self.redirect_uri
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save token
        self._save_credentials(credentials)
        
        return {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_at": credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    def _save_credentials(self, credentials: Credentials):
        """Save credentials to file."""
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }
        os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
        with open(self.token_file, 'w') as f:
            json.dump(token_data, f)
    
    def load_credentials(self) -> Optional[Credentials]:
        """Load credentials from file."""
        if not os.path.exists(self.token_file):
            return None
        
        with open(self.token_file, 'r') as f:
            token_data = json.load(f)
        
        credentials = Credentials(
            token=token_data['token'],
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data['token_uri'],
            client_id=token_data['client_id'],
            client_secret=token_data['client_secret'],
            scopes=token_data['scopes']
        )
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._save_credentials(credentials)
        
        return credentials
    
    def get_gsc_service(self) -> Optional[build]:
        """Get Google Search Console API service."""
        credentials = self.load_credentials()
        if not credentials:
            return None
        return build('webmasters', 'v3', credentials=credentials)
    
    def get_indexing_service(self) -> Optional[build]:
        """Get Indexing API service."""
        credentials = self.load_credentials()
        if not credentials:
            return None
        return build('indexing', 'v3', credentials=credentials)
    
    def get_drive_service(self) -> Optional[build]:
        """Get Google Drive API service."""
        credentials = self.load_credentials()
        if not credentials:
            return None
        return build('drive', 'v3', credentials=credentials)
    
    def get_sheets_service(self) -> Optional[build]:
        """Get Google Sheets API service."""
        credentials = self.load_credentials()
        if not credentials:
            return None
        return build('sheets', 'v4', credentials=credentials)
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.load_credentials() is not None
