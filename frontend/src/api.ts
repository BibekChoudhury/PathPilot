// API client for PathPilot

const API_BASE = '/api/v1';

export interface Profile {
  session_id: string;
  daily_minutes: number;
  language: string;
}

export interface QuestionOption {
  id: string;
  text: string;
}

export interface QuestionPublic {
  id: string;
  version: number;
  skill_id: string;
  purpose: string;
  stem: string;
  options: QuestionOption[];
  ordinal: number;
}

export interface Assessment {
  id: string;
  session_id: string;
  kind: 'diagnostic' | 'practice';
  skill_id?: string;
  status: 'in_progress' | 'completed';
  total_items: number;
  answered_items: number;
  items: QuestionPublic[];
  created_at: string;
  completed_at?: string;
}

export interface AnswerResult {
  answer_id: string;
  question_id: string;
  selected_option: string;
  correctness: boolean;
  correct_option: string;
  distractor_tag?: string;
  explanation: string;
  is_completed: boolean;
  next_question_id?: string;
}

export interface SkillEvidence {
  skill_id: string;
  title: string;
  diagnostic_correct: number;
  diagnostic_attempted: number;
  diagnostic_total: number;
  practice_correct: number;
  practice_attempted: number;
  practice_total: number;
  status: 'needs_practice' | 'proficient' | 'not_assessed';
  evidence_caveat: string;
  misconceptions: string[];
}

export interface Task {
  id: string;
  plan_id: string;
  skill_id: string;
  kind: 'learn' | 'practice' | 'review';
  minutes: number;
  status: 'pending' | 'completed' | 'skipped';
  title: string;
  description: string;
  source_task_id?: string;
}

export interface DeferredTask {
  skill_id: string;
  kind: string;
  minutes: number;
  title: string;
  reason: string;
}

export interface Plan {
  id: string;
  session_id: string;
  version: number;
  available_minutes: number;
  scheduled_minutes: number;
  reason: string;
  created_at: string;
  tasks: Task[];
  deferred_tasks?: DeferredTask[];
}

export interface PlanDiff {
  previous_version: number;
  new_version: number;
  added_tasks: string[];
  removed_tasks: string[];
  retained_tasks: string[];
  minutes_diff: number;
}

export interface ReplanResult {
  status: string;
  action: string;
  previous_version: number;
  plan_version: number;
  available_minutes: number;
  scheduled_minutes: number;
  tasks: Task[];
  deferred_tasks: DeferredTask[];
  diff: PlanDiff;
  warnings: string[];
}

export interface ProgressData {
  session_id: string;
  profile: Profile;
  skills: SkillEvidence[];
  current_plan?: Plan;
  diagnostic_completed: boolean;
}

export interface AgentRun {
  run_id: string;
  session_id: string;
  status: string;
  requested_action: string;
  tool_result?: any;
  reply_text: string;
  llm_mode: string;
  error_code?: string;
  created_at: string;
}

export interface ProgramComparisonRow {
  institution: string;
  program: string;
  opening_rank: number;
  closing_rank: number;
  status: 'at_or_better' | 'outside';
  difference: number;
}

export interface ScenarioResult {
  rank: number;
  cohort_key: string;
  cohort_name: string;
  year: number;
  round: number;
  rank_type: string;
  quota: string;
  seat_category: string;
  source_url: string;
  retrieved_at: string;
  rows: ProgramComparisonRow[];
  disclaimer: string;
}

function getHeaders(extraHeaders: Record<string, string> = {}): HeadersInit {
  return { 'Content-Type': 'application/json', ...extraHeaders };
}

async function responseError(res: Response, fallback: string): Promise<Error> {
  const { detail } = await res.json().catch(() => ({}));
  const message = typeof detail === 'string' ? detail : detail?.message;
  return new Error(typeof message === 'string' ? message : fallback);
}

async function fetchProgress(allowMissing: boolean): Promise<ProgressData | null> {
  const res = await fetch(API_BASE + '/progress', { credentials: 'include' });
  if (allowMissing && res.status === 401) return null;
  if (!res.ok) throw await responseError(res, 'Failed to fetch progress');
  return res.json();
}

async function createSession(): Promise<{ profile: Profile }> {
  const res = await fetch(API_BASE + '/demo-sessions', { method: 'POST', credentials: 'include' });
  if (!res.ok) throw await responseError(res, 'Failed to create demo session');
  return res.json();
}

let pendingInitialization: Promise<ProgressData> | null = null;

export const api = {
  initSession(): Promise<ProgressData> {
    if (!pendingInitialization) {
      pendingInitialization = (async () => {
        const current = await fetchProgress(true);
        if (current) return current;
        await createSession();
        return (await fetchProgress(false))!;
      })().finally(() => { pendingInitialization = null; });
    }
    return pendingInitialization;
  },

  resetSession: createSession,

  async updateProfile(daily_minutes: number): Promise<Profile> {
    const res = await fetch(`${API_BASE}/profile`, {
      method: 'PUT',
      headers: getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ daily_minutes })
    });
    if (!res.ok) throw new Error('Failed to update profile');
    return res.json();
  },

  async getProgress(): Promise<ProgressData> {
    return (await fetchProgress(false))!;
  },

  async startAssessment(kind: 'diagnostic' | 'practice', skill_id?: string): Promise<Assessment> {
    const res = await fetch(`${API_BASE}/assessments`, {
      method: 'POST',
      headers: getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ kind, skill_id })
    });
    if (!res.ok) throw new Error('Failed to start assessment');
    return res.json();
  },

  async getAssessment(id: string): Promise<Assessment> {
    const res = await fetch(`${API_BASE}/assessments/${id}`, {
      headers: getHeaders(),
      credentials: 'include'
    });
    if (!res.ok) throw new Error('Failed to fetch assessment');
    return res.json();
  },

  async submitAnswer(
    assessmentId: string,
    questionId: string,
    selectedOption: string,
    idempotencyKey?: string
  ): Promise<AnswerResult> {
    const extraHeaders: Record<string, string> = {};
    if (idempotencyKey) {
      extraHeaders['Idempotency-Key'] = idempotencyKey;
    }

    const res = await fetch(`${API_BASE}/assessments/${assessmentId}/answers`, {
      method: 'POST',
      headers: getHeaders(extraHeaders),
      credentials: 'include',
      body: JSON.stringify({ question_id: questionId, selected_option: selectedOption })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Answer submission failed' }));
      throw new Error(err.detail || 'Answer submission failed');
    }
    return res.json();
  },

  async getAssessmentResults(assessmentId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/assessments/${assessmentId}/results`, {
      headers: getHeaders(),
      credentials: 'include'
    });
    if (!res.ok) throw new Error('Failed to fetch results');
    return res.json();
  },

  async createPlan(availableMinutes?: number): Promise<Plan> {
    const res = await fetch(`${API_BASE}/plans`, {
      method: 'POST',
      headers: getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ available_minutes: availableMinutes })
    });
    if (!res.ok) throw new Error('Failed to generate plan');
    return res.json();
  },

  async replan(availableMinutes: number, expectedVersion: number, reason?: string): Promise<ReplanResult> {
    const res = await fetch(`${API_BASE}/plans/replan`, {
      method: 'POST',
      headers: getHeaders({ 'Idempotency-Key': `replan-${Date.now()}` }),
      credentials: 'include',
      body: JSON.stringify({
        available_minutes: availableMinutes,
        expected_version: expectedVersion,
        reason: reason || 'Manual replan request'
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Replanning failed' }));
      throw new Error(err.detail?.message || err.detail || 'Replanning failed');
    }
    return res.json();
  },

  async updateTaskStatus(taskId: string, status: 'pending' | 'completed' | 'skipped'): Promise<Task> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`, {
      method: 'PATCH',
      headers: getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ status })
    });
    if (!res.ok) throw new Error('Failed to update task status');
    return res.json();
  },

  async runMentor(message: string, expectedPlanVersion?: number): Promise<AgentRun> {
    const res = await fetch(`${API_BASE}/mentor/runs`, {
      method: 'POST',
      headers: getHeaders({ 'Idempotency-Key': crypto.randomUUID() }),
      credentials: 'include',
      body: JSON.stringify({ message, expected_plan_version: expectedPlanVersion })
    });
    if (!res.ok) throw await responseError(res, 'Failed to run mentor');
    return res.json();
  },

  async compareRank(rank: number, cohortKey: string = 'nitt_crl_open_os_2024', rankType: string = 'CRL'): Promise<ScenarioResult> {
    const res = await fetch(`${API_BASE}/scenarios/rank`, {
      method: 'POST',
      headers: getHeaders(),
      credentials: 'include',
      body: JSON.stringify({ rank, cohort_key: cohortKey, rank_type: rankType })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Scenario comparison failed' }));
      throw new Error(err.detail || 'Scenario comparison failed');
    }
    return res.json();
  },

  async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('API offline');
    return res.json();
  }
};

