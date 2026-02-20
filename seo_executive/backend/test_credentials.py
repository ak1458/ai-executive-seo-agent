#!/usr/bin/env python3
"""Validate SEO Executive credentials configuration."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("SEO Executive - Credential Validation")
print("=" * 60)
print()

# Check Google Credentials
print("[1/4] Checking Google OAuth Credentials...")
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

google_ok = True

if not client_id or client_id == "your_client_id" or "123456789" in client_id:
    print("  [X] ERROR: GOOGLE_CLIENT_ID is not set or is still a placeholder")
    print("     Get it from: https://console.cloud.google.com/apis/credentials")
    google_ok = False
else:
    print(f"  [OK] Client ID found: {client_id[:30]}...")
    
    if ".apps.googleusercontent.com" not in client_id:
        print("  [X] ERROR: Client ID format is wrong")
        print("     Should end with: .apps.googleusercontent.com")
        google_ok = False
    else:
        print("  [OK] Client ID format looks correct")

if not client_secret or client_secret == "your_client_secret" or "GOCSPX-your" in client_secret:
    print("  [X] ERROR: GOOGLE_CLIENT_SECRET is not set or is still a placeholder")
    google_ok = False
else:
    print(f"  [OK] Client Secret found (length: {len(client_secret)})")
    
    if not client_secret.startswith("GOCSPX-"):
        print("  [!]  WARNING: Client Secret doesn't start with GOCSPX-")
        print("     Make sure you copied the OAuth 2.0 secret, not API key")

if redirect_uri != "http://localhost:8000/auth/callback":
    print(f"  [X] ERROR: Redirect URI is wrong: {redirect_uri}")
    print("     Must be exactly: http://localhost:8000/auth/callback")
    google_ok = False
else:
    print("  [OK] Redirect URI is correct")

print()

# Check DataForSEO Credentials
print("[2/4] Checking DataForSEO Credentials...")
dataforseo_login = os.getenv("DATAFORSEO_LOGIN")
dataforseo_password = os.getenv("DATAFORSEO_PASSWORD")

dataforseo_ok = True

if not dataforseo_login or dataforseo_login == "your_login" or dataforseo_login == "your_email@example.com":
    print("  [X] ERROR: DATAFORSEO_LOGIN is not set or is still a placeholder")
    print("     Get it from: https://app.dataforseo.com/api-dashboard")
    dataforseo_ok = False
else:
    print(f"  [OK] Login found: {dataforseo_login}")

if not dataforseo_password or dataforseo_password == "your_password" or dataforseo_password == "your_api_password":
    print("  [X] ERROR: DATAFORSEO_PASSWORD is not set or is still a placeholder")
    dataforseo_ok = False
else:
    print(f"  [OK] Password found (length: {len(dataforseo_password)})")

print()

# Check Ollama
print("[3/4] Checking Ollama Configuration...")
ollama_url = os.getenv("OLLAMA_BASE_URL")
ollama_model = os.getenv("OLLAMA_MODEL")

print(f"  [i]  Ollama URL: {ollama_url}")
print(f"  [i]  Ollama Model: {ollama_model}")
print("  (Verify Ollama is running: curl http://localhost:11434/api/tags)")

print()

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)

if google_ok and dataforseo_ok:
    print("[OK] All credentials are configured!")
    print()
    print("Next steps:")
    print("  1. Restart the backend server")
    print("  2. Open http://localhost:3000")
    print("  3. Click 'Connect Google'")
    print("  4. Complete the OAuth flow")
    sys.exit(0)
else:
    print("[X] Some credentials are missing or invalid")
    print()
    if not google_ok:
        print("Google OAuth Setup:")
        print("  1. Go to: https://console.cloud.google.com/apis/credentials")
        print("  2. Click '+ CREATE CREDENTIALS' -> 'OAuth client ID'")
        print("  3. Application type: Web application")
        print("  4. Add redirect URI: http://localhost:8000/auth/callback")
        print("  5. Copy Client ID and Secret to backend/.env")
        print()
    if not dataforseo_ok:
        print("DataForSEO Setup:")
        print("  1. Go to: https://dataforseo.com/ and create account")
        print("  2. Get API credentials from: https://app.dataforseo.com/api-dashboard")
        print("  3. Copy Login and Password to backend/.env")
    sys.exit(1)
