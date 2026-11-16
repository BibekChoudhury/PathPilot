from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- Profile & Session ---
class ProfileOut(BaseModel):
    session_id: str
    daily_minutes: int = Field(default=45, ge=15, le=240)
    language: str = "en"


class ProfileUpdate(BaseModel):
    daily_minutes: Optional[int] = Field(None, ge=15, le=240)
    language: Optional[str] = None


class DemoSessionOut(BaseModel):
    session_id: str
    token: str
    created_at: str
    expires_at: str
    profile: ProfileOut


# --- Question & Assessment ---
class QuestionOption(BaseModel):
    id: str
    text: str


class QuestionPublic(BaseModel):
    id: str
    version: int
    skill_id: str
    purpose: str
    stem: str
    options: List[QuestionOption]
    ordinal: int


class AssessmentCreate(BaseModel):
    kind: str = Field(..., pattern="^(diagnostic|practice)$")
    skill_id: Optional[str] = None


class AssessmentOut(BaseModel):
    id: str
    session_id: str
    kind: str
    skill_id: Optional[str] = None
    status: str
    total_items: int
    answered_items: int
    items: List[QuestionPublic]
    created_at: str
    completed_at: Optional[str] = None


class AnswerSubmit(BaseModel):
    question_id: str
    selected_option: str = Field(..., min_length=1, max_length=1, pattern="^[A-Da-d]$")
    skipped: bool = False


class AnswerResult(BaseModel):
    answer_id: str
    question_id: str
    selected_option: str
    correctness: bool
    correct_option: str
    distractor_tag: Optional[str] = None
    explanation: str
    is_completed: bool
    next_question_id: Optional[str] = None


class SkillEvidence(BaseModel):
    skill_id: str
    title: str
    diagnostic_correct: int
    diagnostic_attempted: int
    diagnostic_total: int
    practice_correct: int
    practice_attempted: int
    practice_total: int
    status: str  # "needs_practice", "proficient", "not_assessed"
    evidence_caveat: str
    misconceptions: List[str]


class AssessmentResultOut(BaseModel):
    assessment_id: str
    kind: str
    status: str
    total_items: int
    answered_items: int
    skills: List[SkillEvidence]
    caveats: List[str]


# --- Planning ---
class TaskOut(BaseModel):
    id: str
    plan_id: str
    skill_id: str
    kind: str  # "learn", "practice", "review"
    minutes: int
    status: str  # "pending", "completed", "skipped"
    title: str
    description: str
    source_task_id: Optional[str] = None


class DeferredTaskOut(BaseModel):
    skill_id: str
    kind: str
    minutes: int
    title: str
    reason: str


class TaskStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|completed|skipped)$")


class PlanCreate(BaseModel):
    available_minutes: Optional[int] = Field(None, ge=15, le=240)
    goal: Optional[str] = None


class PlanDiffOut(BaseModel):
    previous_version: int
    new_version: int
    added_tasks: List[str]
    removed_tasks: List[str]
    retained_tasks: List[str]
    minutes_diff: int


class PlanOut(BaseModel):
    id: str
    session_id: str
    version: int
    available_minutes: int
    scheduled_minutes: int
    reason: str
    created_at: str
    tasks: List[TaskOut]
    deferred_tasks: List[DeferredTaskOut] = []


class ReplanRequest(BaseModel):
    available_minutes: int = Field(..., ge=15, le=240)
    reason: str = "Adjusted daily availability"
    expected_version: int


class ReplanResponse(BaseModel):
    status: str = "completed"
    action: str = "replan"
    previous_version: int
    plan_version: int
    available_minutes: int
    scheduled_minutes: int
    tasks: List[TaskOut]
    deferred_tasks: List[DeferredTaskOut]
    diff: PlanDiffOut
    warnings: List[str]


# --- Progress Overview ---
class ProgressOut(BaseModel):
    session_id: str
    profile: ProfileOut
    skills: List[SkillEvidence]
    current_plan: Optional[PlanOut] = None
    diagnostic_completed: bool


# --- Mentor & Agent ---
class MentorRunRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    expected_plan_version: Optional[int] = Field(None, ge=0)


class AgentRunOut(BaseModel):
    run_id: str
    session_id: str
    status: str  # "completed", "failed", "fallback"
    requested_action: str
    tool_result: Optional[Dict[str, Any]] = None
    reply_text: str
    llm_mode: str
    error_code: Optional[str] = None
    created_at: str


# --- Historical Scenarios ---
class ScenarioRequest(BaseModel):
    rank: int = Field(..., gt=0)
    cohort_key: str
    rank_type: Optional[str] = "CRL"


class ProgramComparisonRow(BaseModel):
    institution: str
    program: str
    opening_rank: int
    closing_rank: int
    status: str  # "at_or_better" | "outside"
    difference: int


class ScenarioResultOut(BaseModel):
    rank: int
    cohort_key: str
    cohort_name: str
    year: int
    round: int
    rank_type: str
    quota: str
    seat_category: str
    source_url: str
    retrieved_at: str
    rows: List[ProgramComparisonRow]
    disclaimer: str

