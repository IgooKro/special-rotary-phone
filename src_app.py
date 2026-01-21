"""
High School Management System API

A simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""
from pathlib import Path
from threading import Lock
from typing import Dict, List

from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount the static files directory (use Path consistently)
current_dir = Path(__file__).parent
static_dir = current_dir / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# In-memory activity database
activities: Dict[str, Dict] = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Join the competitive basketball team and compete in regional tournaments",
        "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["james@mergington.edu"],
    },
    "Tennis Club": {
        "description": "Learn tennis skills and participate in friendly matches",
        "schedule": "Wednesdays and Saturdays, 3:00 PM - 4:30 PM",
        "max_participants": 12,
        "participants": ["lucas@mergington.edu", "sophia@mergington.edu"],
    },
    "Drama Club": {
        "description": "Perform in school plays and theatrical productions",
        "schedule": "Tuesdays and Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": ["isabella@mergington.edu", "alexander@mergington.edu"],
    },
    "Art Studio": {
        "description": "Explore various art techniques including painting, drawing, and sculpture",
        "schedule": "Mondays and Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": ["ava@mergington.edu"],
    },
    "Robotics Club": {
        "description": "Build and program robots to compete in robotics competitions",
        "schedule": "Thursdays and Saturdays, 3:00 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["noah@mergington.edu", "liam@mergington.edu"],
    },
    "Science Club": {
        "description": "Conduct experiments and explore scientific concepts through hands-on activities",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": ["charlotte@mergington.edu"],
    },
}

# Protect modifications to the in-memory store for thread-safety
_db_lock = Lock()


class SignupRequest(BaseModel):
    email: EmailStr


@app.get("/")
def root():
    """Redirect to the static front-end index page."""
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    """Return all activities (note: this is the in-memory view)."""
    return activities


@app.get("/activities/{activity_name}")
def get_activity(activity_name: str):
    """Return details for a single activity."""
    activity = activities.get(activity_name)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return activity


def validate_student(email: str) -> bool:
    """Very small domain validation for the example school."""
    return email.lower().endswith("@mergington.edu")


def check_already_signed_up(activity_name: str, email: str) -> bool:
    """Return True if the email is already a participant of the activity."""
    activity = activities.get(activity_name)
    if not activity:
        return False
    return email in activity["participants"]


@app.post("/activities/{activity_name}/signup", status_code=status.HTTP_201_CREATED)
def signup_for_activity(activity_name: str, payload: SignupRequest):
    """
    Sign up a student for an activity.

    Validations performed:
    - activity exists -> 404
    - email is from mergington.edu -> 400
    - not already signed up -> 409
    - activity not full -> 403
    """
    email = payload.email.lower()

    if not validate_student(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email must be a @mergington.edu address")

    with _db_lock:
        activity = activities.get(activity_name)
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

        if email in activity["participants"]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Student already signed up for this activity")

        if len(activity["participants"]) >= activity["max_participants"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Activity is full")

        activity["participants"].append(email)

    return {"message": f"Signed up {email} for {activity_name}"}