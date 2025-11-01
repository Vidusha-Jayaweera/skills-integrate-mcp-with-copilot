"""Mergington High School - API backed by SQLModel persisted storage.

This version replaces the in-memory activities dict with a small SQLite
backed (configurable) database using SQLModel. By default it will create
`./dev.db` locally. You can set `DATABASE_URL` to a postgres URL for
production.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from typing import Dict

from sqlmodel import select

from .db import create_db_and_tables, get_session
from .models import Activity, Signup


app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount static files (same as before)
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")


def _initial_activity_data() -> Dict[str, dict]:
    # Original seed data preserved here for the initial migration
    return {
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
        "Soccer Team": {
            "description": "Join the school soccer team and compete in matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 22,
            "participants": ["liam@mergington.edu", "noah@mergington.edu"],
        },
        "Basketball Team": {
            "description": "Practice and play basketball with the school team",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["ava@mergington.edu", "mia@mergington.edu"],
        },
        "Art Club": {
            "description": "Explore your creativity through painting and drawing",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
        },
        "Drama Club": {
            "description": "Act, direct, and produce plays and performances",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
        },
        "Math Club": {
            "description": "Solve challenging problems and participate in math competitions",
            "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
            "max_participants": 10,
            "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
        },
        "Debate Team": {
            "description": "Develop public speaking and argumentation skills",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 12,
            "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
        },
    }


@app.on_event("startup")
def on_startup() -> None:
    # Create DB/tables and seed initial activities if empty
    create_db_and_tables()
    with get_session() as session:
        activity_count = session.exec(select(Activity)).first()
        if activity_count is None:
            seed = _initial_activity_data()
            for name, info in seed.items():
                activity = Activity(
                    name=name,
                    description=info["description"],
                    schedule=info["schedule"],
                    max_participants=info["max_participants"],
                )
                session.add(activity)
                session.commit()
                # add pre-existing participants as signups
                for email in info.get("participants", []):
                    signup = Signup(activity_id=activity.id, email=email)
                    session.add(signup)
                session.commit()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    """Return activities in the same shape as the original API to avoid
    changing the frontend.
    """
    with get_session() as session:
        activities = {}
        results = session.exec(select(Activity)).all()
        for act in results:
            # fetch signups for this activity
            signups = session.exec(select(Signup).where(Signup.activity_id == act.id)).all()
            participants = [s.email for s in signups]
            activities[act.name] = {
                "description": act.description,
                "schedule": act.schedule,
                "max_participants": act.max_participants,
                "participants": participants,
            }
        return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity (persisted)."""
    with get_session() as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        # current participants
        signups = session.exec(select(Signup).where(Signup.activity_id == activity.id)).all()
        participants = [s.email for s in signups]
        if email in participants:
            raise HTTPException(status_code=400, detail="Student is already signed up")

        if len(participants) >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        signup = Signup(activity_id=activity.id, email=email)
        session.add(signup)
        session.commit()
        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity (persisted)."""
    with get_session() as session:
        activity = session.exec(select(Activity).where(Activity.name == activity_name)).first()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        signup = session.exec(
            select(Signup).where((Signup.activity_id == activity.id) & (Signup.email == email))
        ).first()
        if not signup:
            raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

        session.delete(signup)
        session.commit()
        return {"message": f"Unregistered {email} from {activity_name}"}
