export type TestCaseCategory =
  | 'Functional'
  | 'Negative'
  | 'Boundary Value'
  | 'Validation'
  | 'Regression'
  | 'Smoke'
  | 'API'
  | 'Accessibility'
  | 'Visual'
  | 'Exploratory';

export type Priority = 'low' | 'medium' | 'high' | 'critical';
export type RiskLevel = 'low' | 'medium' | 'high';
export type AutomationStatus = 'manual_only' | 'automated' | 'candidate' | 'in_progress';
export type ApprovalStatus = 'draft' | 'in_review' | 'approved' | 'archived';
export type Provenance = 'observed' | 'source_code' | 'ai_inferred' | 'manual';
export type ActionType =
  | 'goto'
  | 'click'
  | 'fill'
  | 'press'
  | 'select_option'
  | 'assert_visible'
  | 'assert_text'
  | 'assert_url'
  | 'wait_for';

export interface TestStepSpec {
  step_number: number;
  action_type: ActionType;
  description: string;
  target_locator?: string;
  input_value?: string;
  expected_result: string;
  timeout_ms?: number;
}

export interface TestCaseSpec {
  code_identifier: string;
  title: string;
  objective: string;
  category: TestCaseCategory;
  priority: Priority;
  risk_level: RiskLevel;
  automation_status: AutomationStatus;
  provenance: Provenance;
  ai_confidence_score?: number | null;
  preconditions: string[];
  test_data: Record<string, any>;
  steps: TestStepSpec[];
  expected_result: string;
}

export type RunStatus =
  | 'queued'
  | 'starting'
  | 'running'
  | 'passed'
  | 'failed'
  | 'blocked'
  | 'cancelled'
  | 'timed_out'
  | 'flaky';

export interface TestRunSummary {
  id: string;
  project_id: string;
  status: RunStatus;
  trigger: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  duration_ms: number;
  started_at?: string;
  completed_at?: string;
}

export interface ProjectSummary {
  id: string;
  name: string;
  description?: string;
  target_url: string;
  github_repo?: string;
  environment: string;
  status: string;
  created_at: string;
}
