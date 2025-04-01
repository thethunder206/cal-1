from flask import Flask, redirect, request, session, jsonify, url_for
import os
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Change this for security

# Google OAuth Config
CLIENT_ID = "357347057692-lpmistphf2al5cqfttgvmbmhjobb9hgk.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "https://cal-1-dv3f.onrender.com/callback"  # ✅ Updated URL
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Google OAuth flow setup
def get_google_auth_flow():
    return google_auth_oauthlib.flow.Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES
    )

@app.route("/")
def home():
    return "Google Calendar OAuth Backend Running"

@app.route("/login")
def login():
    flow = get_google_auth_flow()
    flow.redirect_uri = REDIRECT_URI
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    session["state"] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    if "state" not in session:
        return "Session state not found", 400

    flow = get_google_auth_flow()
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    session["credentials"] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }

    return redirect(url_for("get_calendar"))

@app.route("/calendar")
def get_calendar():
    if "credentials" not in session:
        return redirect(url_for("login"))

    credentials = google.oauth2.credentials.Credentials(**session["credentials"])
    service = googleapiclient.discovery.build("calendar", "v3", credentials=credentials)

    events_result = service.events().list(
        calendarId="primary", maxResults=10, singleEvents=True,
        orderBy="startTime"
    ).execute()
    events = events_result.get("items", [])

    return jsonify(events)

if __name__ == "__main__":
    from waitress import serve  # Use Waitress instead of Gunicorn for Render
    serve(app, host="0.0.0.0", port=8080)

