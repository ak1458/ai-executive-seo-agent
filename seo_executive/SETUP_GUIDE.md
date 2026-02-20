# SEO Executive - Setup Guide

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Ollama installed and running (`ollama list` shows models)
- [ ] Node.js 18+ installed (for frontend dev)
- [ ] Redis installed (optional, for background tasks)

---

## Step 1: Google Cloud OAuth Setup (Required for GSC, Drive, Indexing)

### 1.1 Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable billing (required for some APIs)

### 1.2 Enable APIs
Go to **APIs & Services → Library** and enable:
- ✅ Google Search Console API
- ✅ Indexing API
- ✅ Google Drive API
- ✅ Google Sheets API

### 1.3 Configure OAuth Consent Screen
1. Go to **APIs & Services → OAuth consent screen**
2. Select **External** (or Internal if using Google Workspace)
3. Fill in required fields:
   - App name: `SEO Executive`
   - User support email: your email
   - Developer contact information: your email
4. Click **SAVE AND CONTINUE** through all tabs (Scopes, Test users)
5. Click **BACK TO DASHBOARD**
6. Click **PUBLISH APP** → Confirm

### 1.4 Create OAuth 2.0 Credentials
1. Go to **APIs & Services → Credentials**
2. Click **+ CREATE CREDENTIALS → OAuth client ID**
3. Application type: **Web application**
4. Name: `SEO Executive Local`
5. Authorized redirect URIs:
   ```
   http://localhost:8000/auth/callback
   ```
6. Click **CREATE**
7. **COPY** the Client ID and Client Secret shown in the popup

### 1.5 Update .env File
Edit `backend/.env`:
```env
GOOGLE_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_actual_secret_here
```

**IMPORTANT:**
- NO quotes around values
- NO spaces before/after `=`
- Client ID must end with `.apps.googleusercontent.com`

---

## Step 2: DataForSEO Setup (Required for Rank Tracking & Keywords)

### 2.1 Create Account
1. Go to https://dataforseo.com/
2. Sign up for an account
3. Verify email

### 2.2 Get API Credentials
1. Go to https://app.dataforseo.com/api-dashboard
2. Find your **Login** (email) and **Password**
3. Note: This is NOT your account password - it's the API password shown in the dashboard

### 2.3 Update .env File
Edit `backend/.env`:
```env
DATAFORSEO_LOGIN=your_email@example.com
DATAFORSEO_PASSWORD=your_api_password_from_dashboard
```

---

## Step 3: Start the Application

### Terminal 1: Backend
```powershell
cd "d:\gravity\Ai executive\seo_executive"
.\start.ps1
```

### Terminal 2: Frontend
```powershell
cd "d:\gravity\Ai executive\seo_executive"
.\start-frontend.ps1
```

---

## Step 4: Verify Everything Works

### 4.1 Check Backend Health
Open: http://localhost:8000/health

Expected response:
```json
{"status":"healthy","google_authenticated":false,"version":"1.0.0"}
```

### 4.2 Open Dashboard
Go to: http://localhost:3000

### 4.3 Connect Google Account
1. Click **"Connect Google"** button
2. Complete OAuth flow
3. Health check should show: `"google_authenticated":true`

### 4.4 Test Features

#### Test 1: Technical Audit (No credentials needed)
1. Go to **Audits** tab
2. Enter URL: `https://example.com`
3. Click **Start Audit**
4. Check job panel for progress

#### Test 2: Keyword Research (Needs DataForSEO)
1. Go to **Keywords** tab
2. Enter seed keyword: `best running shoes`
3. Click **Start Research**

#### Test 3: GSC Sync (Needs Google Auth)
1. Go to **Websites** tab
2. Add your verified GSC website
3. Click **Sync GSC Data**

---

## Troubleshooting

### "invalid_client" Error
- Double-check Client ID/Secret in `.env`
- No quotes, no spaces
- Must be Web application type (not Desktop)
- Redirect URI must match exactly

### "unauthorized_client" Error
- OAuth consent screen must be published (not Testing)
- Or add your email as a Test user

### "access_denied" Error
- User clicked "Cancel" on consent screen
- App not verified by Google (normal for localhost)
- Click "Continue" on the warning screen

### Database Errors
```powershell
cd backend
mkdir -p data
.\venv\Scripts\python.exe -c "from app.models.database import init_db; init_db()"
```

### Port Already in Use
```powershell
# Kill process on port 8000
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Kill process on port 3000
Get-NetTCPConnection -LocalPort 3000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

---

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/auth/google` | GET | Get OAuth URL |
| `/auth/callback` | GET | OAuth callback |
| `/auth/status` | GET | Check auth status |
| `/task` | POST | Submit new task |
| `/task/{id}` | GET | Check task status |
| `/websites` | GET/POST | List/Add websites |
| `/keywords/research` | POST | Start keyword research |
| `/indexing/submit` | POST | Submit URLs for indexing |
| `/rankings/check` | POST | Check keyword rankings |

Full API docs: http://localhost:8000/docs

---

## Next Steps After Setup

1. **Add your first website** via the dashboard
2. **Run a technical audit** to test the crawler
3. **Connect Google Search Console** to pull real data
4. **Set up scheduled tasks** in Celery for weekly reports
5. **Customize the AI prompts** in `ollama_service.py` for your needs

---

## Support

If you encounter issues:
1. Check logs in terminal running the backend
2. Verify all credentials are correctly formatted
3. Ensure Ollama is running: `ollama list`
4. Test APIs directly: http://localhost:8000/docs
