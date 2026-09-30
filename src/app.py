"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import os
import time
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from pydantic import BaseModel

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

SESSION_COOKIE_NAME = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60


class TeacherCredentials(BaseModel):
    username: str
    password: str


def is_valid_session(token: str | None) -> bool:
    secret = os.environ.get("SESSION_SECRET")
    if not token or not secret or len(secret) < 32:
        return False

    try:
        expires_at, signature = token.rsplit(".", 1)
        if int(expires_at) <= int(time.time()):
            return False
    except ValueError:
        return False

    expected_signature = hmac.new(
        secret.encode(), expires_at.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


def require_teacher(request: Request) -> None:
    if not is_valid_session(request.cookies.get(SESSION_COOKIE_NAME)):
        raise HTTPException(status_code=401, detail="Teacher login required")


def create_session_token() -> str:
    secret = os.environ.get("SESSION_SECRET")
    if not secret or len(secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="Set SESSION_SECRET to a random value of at least 32 characters",
        )

    expires_at = str(int(time.time()) + SESSION_DURATION_SECONDS)
    signature = hmac.new(
        secret.encode(), expires_at.encode(), hashlib.sha256
    ).hexdigest()
    return f"{expires_at}.{signature}"

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.get("/auth/session")
def get_auth_session(request: Request):
    return {"authenticated": is_valid_session(
        request.cookies.get(SESSION_COOKIE_NAME)
    )}


@app.post("/auth/login")
def login(credentials: TeacherCredentials, response: Response):
    username = os.environ.get("TEACHER_USERNAME")
    password = os.environ.get("TEACHER_PASSWORD")
    if not username or not password:
        raise HTTPException(
            status_code=503,
            detail="Set TEACHER_USERNAME and TEACHER_PASSWORD to enable teacher login",
        )

    if not (
        hmac.compare_digest(credentials.username, username)
        and hmac.compare_digest(credentials.password, password)
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(),
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
        samesite="strict",
        path="/",
    )
    return {"message": "Logged in"}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
        samesite="strict",
        path="/",
    )
    return {"message": "Logged out"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str, email: str, _: None = Depends(require_teacher)
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str, email: str, _: None = Depends(require_teacher)
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
