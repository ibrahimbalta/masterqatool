export const getApiBase = (): string => {
  if (typeof window !== 'undefined') {
    // When running in browser (Codespaces, Vercel, localhost):
    // Use relative path so Next.js rewrites proxy requests directly to backend without CORS or mixed-content issues
    if (process.env.NEXT_PUBLIC_API_URL && !process.env.NEXT_PUBLIC_API_URL.includes('localhost')) {
      return process.env.NEXT_PUBLIC_API_URL;
    }
    return '/api/v1';
  }
  // SSR (inside node.js runtime)
  return process.env.INTERNAL_API_URL || 'http://127.0.0.1:8000/api/v1';
};

const API_BASE = getApiBase();

export interface Project {
  id: string;
  name: string;
  description?: string;
  target_url: string;
  github_repo?: string;
  environment: string;
  status: string;
  created_at: string;
}

export interface TestCase {
  id: string;
  project_id: string;
  code_identifier: string;
  title: string;
  objective?: string;
  category: string;
  priority: string;
  risk_level: string;
  automation_status: string;
  approval_status: string;
  current_version: number;
  ai_confidence_score?: number | null;
  provenance: string;
  latest_spec: {
    preconditions?: string[];
    steps?: Array<{
      step_number: number;
      action_type: string;
      target_locator?: string;
      input_value?: string;
      expected_result: string;
    }>;
    expected_result?: string;
  };
  created_at: string;
}

export interface TestRun {
  id: string;
  project_id: string;
  organization_id: string;
  trigger: string;
  status: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  duration_ms: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  results: Array<{
    id: string;
    test_case_id: string;
    test_case_code?: string;
    test_case_title?: string;
    status: string;
    duration_ms: number;
    error_message?: string;
    steps: Array<{
      id: string;
      step_number: number;
      action_type: string;
      target_locator?: string;
      status: string;
      expected_result?: string;
      actual_result?: string;
      error_message?: string;
      duration_ms: number;
    }>;
    artifacts: Array<{
      id: string;
      artifact_type: string;
      storage_path: string;
      mime_type: string;
    }>;
    locator_repairs?: LocatorRepair[];
  }>;
}

export interface Bug {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  severity: string;
  reproduction_steps: string[];
  expected_behavior?: string;
  actual_behavior?: string;
  root_cause_hypothesis?: string;
  verified_cause?: string;
  status: string;
  created_at: string;
}

export interface TestSuite {
  id: string;
  project_id: string;
  name: string;
  description?: string;
  category: string;
  total_cases: number;
  created_at: string;
  updated_at: string;
  test_cases?: TestCase[];
}

export interface LocatorRepair {
  id: string;
  test_result_id: string;
  test_case_id: string;
  step_number: number;
  original_locator: string;
  suggested_locator: string;
  strategy: string;
  confidence_score: number;
  dom_snippet?: string;
  status: string;
  created_at: string;
}

export interface TeamMember {
  id: string;
  user_id: string;
  email: string;
  full_name?: string;
  role: string;
  created_at: string;
}

export interface AutomationCode {
  project_id: string;
  project_name: string;
  language: string;
  runner: string;
  total_test_cases: number;
  code: string;
}

export interface IntegrationConnection {
  id: string;
  project_id: string;
  connection_type: string;
  status: string;
  last_verified_at?: string;
  created_at: string;
}

export interface UsageSummary {
  plan_tier: string;
  test_minutes_used: number;
  test_minutes_limit: number;
  projects_count: number;
  projects_limit: number;
  ai_tokens_used: number;
  ai_tokens_limit: number;
  concurrent_runs_limit: number;
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('ai_qa_token', token);
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      return localStorage.getItem('ai_qa_token');
    }
    return null;
  }

  getBaseUrl(): string {
    return getApiBase();
  }

  private isAuthenticating = false;

  async ensureAuth(): Promise<string | null> {
    const existing = this.getToken();
    if (existing) return existing;

    if (this.isAuthenticating) {
      await new Promise((r) => setTimeout(r, 400));
      return this.getToken();
    }

    this.isAuthenticating = true;
    try {
      const base = this.getBaseUrl();
      const form = new FormData();
      form.append('username', 'architect@acme-qa.com');
      form.append('password', 'SecurePass123!');
      const res = await fetch(`${base}/auth/login`, {
        method: 'POST',
        body: form,
      });

      if (res.ok) {
        const data = await res.json();
        this.setToken(data.access_token);
        return data.access_token;
      }

      // If user does not exist yet, register
      const regRes = await fetch(`${base}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'architect@acme-qa.com',
          password: 'SecurePass123!',
          full_name: 'Lead Architect',
          organization_name: 'Acme QA Corp',
        }),
      });
      if (regRes.ok) {
        const data = await regRes.json();
        this.setToken(data.access_token);
        return data.access_token;
      }
    } catch {
      // ignore
    } finally {
      this.isAuthenticating = false;
    }
    return this.getToken();
  }

  private async request<T>(endpoint: string, options: RequestInit = {}, isRetry = false): Promise<T> {
    let token = this.getToken();
    if (!token && !endpoint.includes('/auth/')) {
      token = await this.ensureAuth();
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const base = this.getBaseUrl();
    const res = await fetch(`${base}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401 && !isRetry && !endpoint.includes('/auth/')) {
      this.setToken('');
      const newToken = await this.ensureAuth();
      if (newToken) {
        return this.request<T>(endpoint, options, true);
      }
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }

    if (res.status === 204) {
      return {} as T;
    }

    return res.json();
  }

  // Auth
  async login(formData: FormData) {
    const res = await fetch(`${this.getBaseUrl()}/auth/login`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail);
    }
    const data = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(email: string, password: string, fullName?: string, orgName?: string) {
    const res = await this.request<{ access_token: string; organization_id: string; role: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName, organization_name: orgName }),
    });
    this.setToken(res.access_token);
    return res;
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    return this.request<Project[]>('/projects');
  }

  async createProject(data: { name: string; target_url: string; description?: string; github_repo?: string; environment?: string }): Promise<Project> {
    return this.request<Project>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async validateUrl(url: string): Promise<{ valid: boolean; message: string; normalized_url?: string }> {
    return this.request<{ valid: boolean; message: string; normalized_url?: string }>('/projects/validate-url', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  }

  // Test Cases
  async getTestCases(projectId: string): Promise<TestCase[]> {
    return this.request<TestCase[]>(`/projects/${projectId}/test-cases`);
  }

  async createTestCase(projectId: string, data: Partial<TestCase>): Promise<TestCase> {
    return this.request<TestCase>(`/projects/${projectId}/test-cases`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTestCase(testCaseId: string, data: Partial<TestCase>): Promise<TestCase> {
    return this.request<TestCase>(`/test-cases/${testCaseId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  getExportCsvUrl(projectId: string): string {
    return `${API_BASE}/projects/${projectId}/test-cases/export`;
  }

  // Test Runs
  async getTestRuns(projectId: string): Promise<TestRun[]> {
    return this.request<TestRun[]>(`/projects/${projectId}/test-runs`);
  }

  async triggerTestRun(projectId: string, testCaseIds?: string[]): Promise<TestRun> {
    return this.request<TestRun>('/test-runs', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, test_case_ids: testCaseIds, trigger: 'manual' }),
    });
  }

  async getTestRun(runId: string): Promise<TestRun> {
    return this.request<TestRun>(`/test-runs/${runId}`);
  }

  async cancelTestRun(runId: string): Promise<TestRun> {
    return this.request<TestRun>(`/test-runs/${runId}/cancel`, {
      method: 'POST',
    });
  }

  // Bugs
  async getBugs(projectId?: string): Promise<Bug[]> {
    const query = projectId ? `?project_id=${projectId}` : '';
    return this.request<Bug[]>(`/bugs${query}`);
  }

  async updateBug(bugId: string, data: Partial<Bug>): Promise<Bug> {
    return this.request<Bug>(`/bugs/${bugId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  // Test Suites
  async getTestSuites(projectId: string): Promise<TestSuite[]> {
    return this.request<TestSuite[]>(`/projects/${projectId}/suites`);
  }

  async createTestSuite(projectId: string, data: { name: string; description?: string; category: string }): Promise<TestSuite> {
    return this.request<TestSuite>(`/projects/${projectId}/suites`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getTestSuite(suiteId: string): Promise<TestSuite> {
    return this.request<TestSuite>(`/suites/${suiteId}`);
  }

  async assignCasesToSuite(suiteId: string, caseIds: string[]): Promise<TestSuite> {
    return this.request<TestSuite>(`/suites/${suiteId}/cases`, {
      method: 'POST',
      body: JSON.stringify(caseIds),
    });
  }

  // Automation Lab
  async getAutomationCode(projectId: string): Promise<AutomationCode> {
    return this.request<AutomationCode>(`/projects/${projectId}/automation/code`);
  }

  getExportPackageUrl(projectId: string): string {
    return `${this.getBaseUrl()}/projects/${projectId}/automation/export-package`;
  }

  // Integrations
  async getIntegrations(projectId: string): Promise<IntegrationConnection[]> {
    return this.request<IntegrationConnection[]>(`/projects/${projectId}/integrations`);
  }

  async connectGitHub(projectId: string, githubRepo: string, githubToken?: string): Promise<any> {
    return this.request<any>(`/projects/${projectId}/integrations/github`, {
      method: 'POST',
      body: JSON.stringify({ github_repo: githubRepo, github_token: githubToken }),
    });
  }

  // Team & Organization
  async getTeamMembers(orgId: string): Promise<TeamMember[]> {
    return this.request<TeamMember[]>(`/organizations/${orgId}/members`);
  }

  async addTeamMember(orgId: string, email: string, role: string): Promise<TeamMember> {
    return this.request<TeamMember>(`/organizations/${orgId}/members`, {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    });
  }

  async removeTeamMember(orgId: string, memberId: string): Promise<void> {
    return this.request<void>(`/organizations/${orgId}/members/${memberId}`, {
      method: 'DELETE',
    });
  }

  // Self-Healing & Locator Repairs
  async getLocatorRepairs(resultId: string): Promise<LocatorRepair[]> {
    return this.request<LocatorRepair[]>(`/test-results/${resultId}/locator-repairs`);
  }

  async updateLocatorRepair(repairId: string, status: string): Promise<LocatorRepair> {
    return this.request<LocatorRepair>(`/locator-repairs/${repairId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  // Artifacts & Evidence
  getArtifactFileUrl(artifactId: string): string {
    return `${this.getBaseUrl()}/artifacts/${artifactId}/file`;
  }

  async getArtifact(artifactId: string): Promise<any> {
    return this.request<any>(`/artifacts/${artifactId}`);
  }

  // Usage
  async getUsage(): Promise<UsageSummary> {
    return this.request<UsageSummary>('/usage');
  }
}

export const api = new ApiClient();
