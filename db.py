import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient 
from pydantic import BaseModel, EmailStr, Field

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Initialize PyMongo Client 
client = MongoClient(MONGODB_URL) 
db = client[DATABASE_NAME]


def get_db():
    """Dependency provider that yields the MongoDB database instance."""
    return db


# =====================================================================
# 1. USER SCHEMAS
# =====================================================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Minimum 6 characters")
    full_name: str = Field(..., min_length=2, description="Full name of the user")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =====================================================================
# 2. SIMULATION SCHEMAS
# =====================================================================

class ImpactScores(BaseModel):
    leadership: int = 0
    technical: int = 0
    problem_solving: int = 0
    communication: int = 0


class SimulationOption(BaseModel):
    option_id: str
    text: str
    feedback: str
    next_step_id: Optional[str] = None  # None indicates terminal decision step
    impact: ImpactScores = Field(default_factory=ImpactScores)


class SimulationStep(BaseModel):
    step_id: str
    title: str
    scenario: str
    options: List[SimulationOption]


class SimulationSchema(BaseModel):
    id: str
    title: str
    domain: str  # e.g., "Software Engineering", "Product Management", "Data Science"
    description: str
    difficulty: str  # "Beginner", "Intermediate", "Advanced"
    estimated_minutes: int
    steps: List[SimulationStep]


class SimulationSummary(BaseModel):
    id: str
    title: str
    domain: str
    description: str
    difficulty: str
    estimated_minutes: int


# =====================================================================
# 3. PROGRESS & DECISION SCHEMAS
# =====================================================================

class DecisionSubmit(BaseModel):
    simulation_id: str
    step_id: str
    option_id: str


class DecisionResult(BaseModel):
    simulation_id: str
    step_id: str
    selected_option_id: str
    feedback: str
    next_step_id: Optional[str] = None
    impact: ImpactScores
    is_completed: bool = False


class SimulationProgress(BaseModel):
    id: Optional[str] = None
    user_id: str
    simulation_id: str
    current_step_id: str
    status: str = "IN_PROGRESS"  # "IN_PROGRESS" or "COMPLETED"
    total_scores: ImpactScores = Field(default_factory=ImpactScores)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DashboardSummary(BaseModel):
    total_simulations_completed: int
    total_simulations_in_progress: int
    overall_scores: ImpactScores
    recent_activity: List[Dict[str, Any]]