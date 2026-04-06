"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.db import Base, engine, SessionLocal, Activity, Participant


app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")


# Create tables if they don't exist (FastAPI startup event)
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency for DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

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



from sqlalchemy.future import select
from fastapi import status
from typing import List, Dict
from sqlalchemy import and_

@app.get("/activities")
async def get_activities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Activity))
    activities = result.scalars().all()
    response = {}
    for activity in activities:
        participants_result = await db.execute(
            select(Participant.email).where(Participant.activity_id == activity.id)
        )
        participants = [row[0] for row in participants_result.all()]
        response[activity.name] = {
            "description": activity.description,
            "schedule": activity.schedule,
            "max_participants": activity.max_participants,
            "participants": participants
        }
    return response



from sqlalchemy.exc import NoResultFound

@app.post("/activities/{activity_name}/signup")
async def signup_for_activity(activity_name: str, email: str, db: AsyncSession = Depends(get_db)):
    """Sign up a student for an activity"""
    # Find the activity
    result = await db.execute(select(Activity).where(Activity.name == activity_name))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check if already signed up
    participant_result = await db.execute(
        select(Participant).where(
            and_(Participant.activity_id == activity.id, Participant.email == email)
        )
    )
    if participant_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Student is already signed up")

    # Add participant
    new_participant = Participant(activity_id=activity.id, email=email)
    db.add(new_participant)
    await db.commit()
    return {"message": f"Signed up {email} for {activity_name}"}



@app.delete("/activities/{activity_name}/unregister")
async def unregister_from_activity(activity_name: str, email: str, db: AsyncSession = Depends(get_db)):
    """Unregister a student from an activity"""
    # Find the activity
    result = await db.execute(select(Activity).where(Activity.name == activity_name))
    activity = result.scalar_one_or_none()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Find the participant
    participant_result = await db.execute(
        select(Participant).where(
            and_(Participant.activity_id == activity.id, Participant.email == email)
        )
    )
    participant = participant_result.scalar_one_or_none()
    if not participant:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    await db.delete(participant)
    await db.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
