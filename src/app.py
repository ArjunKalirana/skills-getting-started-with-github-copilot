"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import motor.motor_asyncio
from typing import Dict, Any

# MongoDB setup
MONGODB_URL = "mongodb+srv://your-connection-string"  # Replace with your MongoDB connection string
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.school_activities
activities_collection = db.activities

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Initial activities data for database population
INITIAL_ACTIVITIES = {
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
    # Sports related activities
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Wednesdays, 4:00 PM - 6:00 PM",
        "max_participants": 22,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Basketball Club": {
        "description": "Practice basketball skills and play friendly games",
        "schedule": "Thursdays, 3:30 PM - 5:30 PM",
        "max_participants": 15,
        "participants": ["liam@mergington.edu", "ava@mergington.edu"]
    },
    # Artistic activities
    "Art Workshop": {
        "description": "Explore painting, drawing, and sculpture techniques",
        "schedule": "Mondays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["ella@mergington.edu", "noah@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act in plays and learn stage performance skills",
        "schedule": "Fridays, 3:30 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["grace@mergington.edu", "jack@mergington.edu"]
    },
    # Intellectual activities
    "Mathletes": {
        "description": "Compete in math competitions and solve challenging problems",
        "schedule": "Tuesdays, 4:00 PM - 5:00 PM",
        "max_participants": 10,
        "participants": ["oliver@mergington.edu", "chloe@mergington.edu"]
    },
    "Science Club": {
        "description": "Conduct experiments and explore scientific concepts",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["benjamin@mergington.edu", "zoe@mergington.edu"]
    }
}

async def init_db():
    """Initialize the database with activities if empty"""
    if await activities_collection.count_documents({}) == 0:
        # Insert all activities
        for name, details in INITIAL_ACTIVITIES.items():
            await activities_collection.insert_one({"_id": name, **details})

@app.on_event("startup")
async def startup_db_client():
    """Initialize the database connection and populate initial data"""
    await init_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    """Close the database connection"""
    client.close()

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
async def get_activities():
    """Get all activities from the database"""
    cursor = activities_collection.find({})
    activities = {}
    async for doc in cursor:
        name = doc.pop("_id")  # Remove _id and use it as the key
        activities[name] = doc
    return activities

@app.post("/activities/{activity_name}/signup")
async def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Check if student is already signed up for any activity
    cursor = activities_collection.find({"participants": email})
    async for _ in cursor:
        raise HTTPException(status_code=400, detail="Student already signed up for an activity")

    # Get the specific activity
    activity = await activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Update participants list
    result = await activities_collection.update_one(
        {"_id": activity_name},
        {"$push": {"participants": email}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update activity")

    return {"message": f"Signed up {email} for {activity_name}"}
