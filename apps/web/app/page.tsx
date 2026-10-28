'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FolderKanban,
  PlaySquare,
  Bug,
  Cpu,
  Clock,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Plus,
  Loader2,
} from 'lucide-react';
import { api, Project, TestRun, Bug as BugType, UsageSummary } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import { ProjectWizardModal } from '@/components/ProjectWizardModal';

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [bugs, setBugs] = useState<BugType[]>([]);
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isWizardOpen, setIsWizardOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // First ensure we have a valid session or demo token
      if (!api.getToken()) {
        try {
          await api.register('architect@acme-qa.com', 'SecurePass123!', 'Lead Architect', 'Acme QA Corp');
        } catch {
          // If user exists, login
          const form = new FormData();
          form.append('username', 'architect@acme-qa.com');
          form.append('password', 'SecurePass123!');
          await api.login(form).catch(() => {});
        }
      }

      const [projs, usageData, bugsData] = await Promise.all([
        api.getProjects().catch(() => []),
        api.getUsage().catch(() => null),
        api.getBugs().catch(() => []),
      ]);

      setProjects(projs);
      setUsage(usageData);
      setBugs(bugsData);

      if (projs.length > 0) {
        const recentRuns = await api.getTestRuns(projs[0].id).catch(() => []);
        setRuns(recentRuns);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to connect to AI QA API backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const totalRuns = runs.length;
  const passedRuns = runs.filter((r) => r.status === 'passed').length;
  const failedRuns = runs.filter((r) => r.status === 'failed').length;
  const criticalBugs = bugs.filter((b) => b.severity === 'critical' || b.severity === 'high').length;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Banner / Hero */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">QA Intelligence Dashboard</h1>
          <p className="text-xs text-zinc-400 mt-1">
            Real-time automated testing metrics, verified Playwright executions, and AI test insights.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsWizardOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-medium shadow-lg shadow-brand-orange/20 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>New QA Project</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>Backend Notice: {error} (Ensure backend API is running on localhost:8000)</span>
          </div>
          <button onClick={loadData} className="underline text-white font-medium hover:text-brand-orange">
            Retry
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center p-16 space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-brand-orange" />
          <p className="text-xs text-zinc-400">Loading live workspace metrics from API...</p>
        </div>
      )}

      {!loading && (
        <>
          {/* Key KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Projects */}
            <div className="p-5 rounded-xl bg-surface-200 border border-border flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-zinc-400">Total Projects</span>
                <div className="w-8 h-8 rounded-lg bg-surface-100 flex items-center justify-center text-zinc-300">
                  <FolderKanban className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4">
                <span className="text-3xl font-bold text-white font-mono">{projects.length}</span>
                <span className="text-[11px] text-zinc-500 block mt-1">Active test environments</span>
              </div>
            </div>

            {/* Total Verified Runs */}
            <div className="p-5 rounded-xl bg-surface-200 border border-border flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-zinc-400">Verified Test Runs</span>
                <div className="w-8 h-8 rounded-lg bg-surface-100 flex items-center justify-center text-zinc-300">
                  <PlaySquare className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4">
                <span className="text-3xl font-bold text-white font-mono">{totalRuns}</span>
                <span className="text-[11px] text-zinc-500 block mt-1">
                  {totalRuns > 0 ? `${passedRuns} passed · ${failedRuns} failed` : 'No runs executed yet'}
                </span>
              </div>
            </div>

            {/* Critical Bugs */}
            <div className="p-5 rounded-xl bg-surface-200 border border-border flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-zinc-400">Open High/Critical Bugs</span>
                <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400">
                  <Bug className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4">
                <span className="text-3xl font-bold text-white font-mono">{criticalBugs}</span>
                <span className="text-[11px] text-zinc-500 block mt-1">
                  {bugs.length} total tracked across all projects
                </span>
              </div>
            </div>

            {/* AI Tokens & Quota */}
            <div className="p-5 rounded-xl bg-surface-200 border border-border flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-zinc-400">AI Usage & Minutes</span>
                <div className="w-8 h-8 rounded-lg bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center text-brand-orange">
                  <Cpu className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-4">
                <span className="text-3xl font-bold text-white font-mono">
                  {usage ? `${usage.test_minutes_used.toFixed(1)}m` : '0m'}
                </span>
                <span className="text-[11px] text-zinc-500 block mt-1">
                  {usage ? `${usage.ai_tokens_used.toLocaleString()} tokens · Plan: ${usage.plan_tier}` : 'Free tier'}
                </span>
              </div>
            </div>
          </div>

          {/* Test Coverage & Verification Integrity Notice */}
          <div className="p-4 rounded-xl bg-surface-300 border border-border flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-surface-100 flex items-center justify-center text-brand-orange shrink-0">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-semibold text-white">Automated Test Coverage Metric</h4>
                <p className="text-[11px] text-zinc-400">
                  In accordance with the True Verification Policy, unverified approximations are never fabricated.
                </p>
              </div>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-surface-200 border border-border text-xs font-mono text-zinc-400">
              Coverage Status:{' '}
              <span className="text-zinc-200 font-semibold">
                {projects.length > 0 && totalRuns > 0 ? 'Evaluating via DOM Discovery' : 'Henüz hesaplanmadı'}
              </span>
            </div>
          </div>

          {/* Recent Runs & Active Projects Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Recent Executions */}
            <div className="lg:col-span-2 bg-surface-200 border border-border rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Recent Playwright Test Runs</h3>
                  <p className="text-[11px] text-zinc-400">Real browser execution traces and step status</p>
                </div>
                <Link
                  href="/execution"
                  className="text-xs text-brand-orange hover:text-brand-orangeHover flex items-center gap-1 font-medium"
                >
                  <span>Execution Center</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {runs.length === 0 ? (
                <div className="p-8 text-center border border-dashed border-border rounded-lg text-zinc-500 text-xs space-y-2">
                  <PlaySquare className="w-8 h-8 mx-auto text-zinc-600" />
                  <p>No test runs executed yet for this project.</p>
                  <p className="text-[11px] text-zinc-600">
                    Create a project and queue test cases to see real-time Playwright results.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-border">
                  {runs.slice(0, 5).map((run) => (
                    <div key={run.id} className="py-3 flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <StatusBadge status={run.status} />
                        <div>
                          <span className="text-xs font-mono text-zinc-300 font-medium">
                            Run #{run.id.slice(0, 8)}
                          </span>
                          <span className="block text-[11px] text-zinc-500">
                            Trigger: {run.trigger} · {run.total_cases} cases
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-xs font-mono text-zinc-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-zinc-500" />
                          {run.duration_ms}ms
                        </span>
                        <Link
                          href="/execution"
                          className="px-2.5 py-1 rounded bg-surface-100 hover:bg-surface-50 text-[11px] text-zinc-200"
                        >
                          View Trace
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Right Col: Projects List */}
            <div className="bg-surface-200 border border-border rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Connected Projects</h3>
                  <p className="text-[11px] text-zinc-400">Target applications under test</p>
                </div>
                <Link
                  href="/projects"
                  className="text-xs text-brand-orange hover:text-brand-orangeHover flex items-center gap-1 font-medium"
                >
                  <span>All Projects</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {projects.length === 0 ? (
                <div className="p-8 text-center border border-dashed border-border rounded-lg text-zinc-500 text-xs space-y-3">
                  <FolderKanban className="w-8 h-8 mx-auto text-zinc-600" />
                  <p>No projects configured yet.</p>
                  <button
                    onClick={() => setIsWizardOpen(true)}
                    className="px-3 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-50 border border-border text-xs text-brand-orange font-medium"
                  >
                    + Add First Project
                  </button>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {projects.slice(0, 5).map((project) => (
                    <div
                      key={project.id}
                      className="p-3 rounded-lg bg-surface-300 border border-border hover:border-brand-orange/40 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-white truncate">{project.name}</span>
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-surface-100 text-zinc-400">
                          {project.environment}
                        </span>
                      </div>
                      <span className="text-[11px] text-zinc-500 truncate block mt-1 font-mono">
                        {project.target_url}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Project Creation Wizard Modal */}
      <ProjectWizardModal
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        onCreated={(newProj) => {
          setProjects((prev) => [newProj, ...prev]);
        }}
      />
    </div>
  );
}
