'use client';

import React, { useEffect, useState } from 'react';
import { PlaySquare, RefreshCw, XCircle, Clock, AlertCircle, Camera, Terminal, ShieldAlert, Loader2 } from 'lucide-react';
import { api, TestRun, Project } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';

export default function ExecutionCenterPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [runs, setRuns] = useState<TestRun[]>([]);
  const [activeRun, setActiveRun] = useState<TestRun | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getProjects().then((projs) => {
      setProjects(projs);
      if (projs.length > 0) {
        setSelectedProjectId(projs[0].id);
      }
    });
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadRuns(selectedProjectId);
    } else {
      setLoading(false);
    }
  }, [selectedProjectId]);

  const loadRuns = async (projId: string) => {
    setLoading(true);
    try {
      const data = await api.getTestRuns(projId);
      setRuns(data);
      if (data.length > 0) {
        setActiveRun(data[0]);
      } else {
        setActiveRun(null);
      }
    } catch {
      setRuns([]);
      setActiveRun(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelRun = async (runId: string) => {
    try {
      const updated = await api.cancelTestRun(runId);
      setRuns((prev) => prev.map((r) => (r.id === runId ? updated : r)));
      if (activeRun?.id === runId) {
        setActiveRun(updated);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to cancel test run');
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Execution Center</h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Isolated browser execution status, step logs, screenshots, and Playwright traces.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => selectedProjectId && loadRuns(selectedProjectId)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-200 hover:bg-surface-100 border border-border text-xs font-medium text-zinc-200 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Project Selector */}
      <div className="flex items-center gap-3 p-4 rounded-xl bg-surface-200 border border-border">
        <span className="text-xs font-medium text-zinc-400">Target Project:</span>
        <select
          value={selectedProjectId}
          onChange={(e) => setSelectedProjectId(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-surface-300 border border-border text-xs text-white focus:outline-none focus:border-brand-orange"
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({p.environment})
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="flex justify-center p-12">
          <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
        </div>
      )}

      {!loading && runs.length === 0 && (
        <div className="p-12 text-center border border-dashed border-border rounded-xl bg-surface-300 space-y-3">
          <PlaySquare className="w-10 h-10 mx-auto text-zinc-600" />
          <h3 className="text-sm font-semibold text-white">No test runs executed</h3>
          <p className="text-xs text-zinc-500 max-w-md mx-auto">
            Queue test scenarios from Test Case Studio to see real-time Playwright execution traces.
          </p>
        </div>
      )}

      {/* Two-Panel Execution Center */}
      {!loading && runs.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Col: Runs History List */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider font-mono">
              Executions ({runs.length})
            </h3>
            <div className="space-y-2">
              {runs.map((r) => {
                const isSelected = activeRun?.id === r.id;
                return (
                  <div
                    key={r.id}
                    onClick={() => setActiveRun(r)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-surface-100 border-brand-orange/50 shadow-md'
                        : 'bg-surface-200 border-border hover:border-zinc-700'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <StatusBadge status={r.status} />
                      <span className="text-[11px] font-mono text-zinc-400 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {r.duration_ms}ms
                      </span>
                    </div>
                    <div className="mt-2 text-xs font-medium text-white font-mono">
                      Run #{r.id.slice(0, 8)}
                    </div>
                    <div className="mt-1 flex items-center justify-between text-[11px] text-zinc-500">
                      <span>{r.total_cases} cases ({r.passed_cases}P / {r.failed_cases}F)</span>
                      <span>{new Date(r.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right 2 Cols: Selected Run Details & Steps */}
          {activeRun && (
            <div className="lg:col-span-2 space-y-4">
              {/* Header Box */}
              <div className="p-5 rounded-xl bg-surface-200 border border-border space-y-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-3">
                      <h2 className="text-base font-semibold text-white font-mono">
                        Run Details: #{activeRun.id}
                      </h2>
                      <StatusBadge status={activeRun.status} />
                    </div>
                    <span className="text-xs text-zinc-400 block mt-1">
                      Triggered by {activeRun.trigger} · Started {new Date(activeRun.created_at).toLocaleString()}
                    </span>
                  </div>

                  {['queued', 'running', 'starting'].includes(activeRun.status) && (
                    <button
                      onClick={() => handleCancelRun(activeRun.id)}
                      className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-medium flex items-center gap-1.5"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Cancel Run</span>
                    </button>
                  )}
                </div>

                {/* KPI mini-bar */}
                <div className="grid grid-cols-4 gap-2 pt-2 border-t border-border text-center">
                  <div className="p-2 rounded-lg bg-surface-300">
                    <span className="text-[10px] text-zinc-500 block">TOTAL CASES</span>
                    <span className="text-sm font-bold text-white font-mono">{activeRun.total_cases}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-surface-300">
                    <span className="text-[10px] text-emerald-500 block">PASSED</span>
                    <span className="text-sm font-bold text-emerald-400 font-mono">{activeRun.passed_cases}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-surface-300">
                    <span className="text-[10px] text-red-500 block">FAILED</span>
                    <span className="text-sm font-bold text-red-400 font-mono">{activeRun.failed_cases}</span>
                  </div>
                  <div className="p-2 rounded-lg bg-surface-300">
                    <span className="text-[10px] text-zinc-500 block">EXECUTION TIME</span>
                    <span className="text-sm font-bold text-zinc-300 font-mono">{activeRun.duration_ms}ms</span>
                  </div>
                </div>
              </div>

              {/* Granular Step Results */}
              <div className="p-5 rounded-xl bg-surface-200 border border-border space-y-4">
                <h3 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider font-mono">
                  Test Case Results & Evidence
                </h3>

                {activeRun.results.length === 0 ? (
                  <div className="p-6 text-center text-xs text-zinc-500 border border-dashed border-border rounded-lg">
                    Awaiting worker to start executing queued test cases...
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activeRun.results.map((res) => (
                      <div key={res.id} className="p-4 rounded-lg bg-surface-300 border border-border space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono font-bold text-white">
                            Case #{res.test_case_id.slice(0, 8)}
                          </span>
                          <StatusBadge status={res.status} />
                        </div>

                        {res.error_message && (
                          <div className="p-2.5 rounded bg-red-500/10 border border-red-500/20 text-xs text-red-400 font-mono">
                            {res.error_message}
                          </div>
                        )}

                        {/* Step breakdown */}
                        {res.steps.length > 0 && (
                          <div className="space-y-1.5 pt-2 border-t border-border">
                            <span className="text-[11px] font-semibold text-zinc-400 block">Execution Steps:</span>
                            {res.steps.map((step) => (
                              <div
                                key={step.id}
                                className="flex items-center justify-between text-xs font-mono py-1 px-2 rounded bg-surface-200"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="text-zinc-600">#{step.step_number}</span>
                                  <span className="text-brand-orange uppercase text-[10px]">{step.action_type}</span>
                                  <span className="text-zinc-300">{step.target_locator}</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] text-zinc-500">{step.duration_ms}ms</span>
                                  <StatusBadge status={step.status} />
                                </div>
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Artifacts (Screenshots, traces) */}
                        {res.artifacts.length > 0 && (
                          <div className="pt-2 flex items-center gap-2">
                            {res.artifacts.map((art) => (
                              <div
                                key={art.id}
                                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-200 border border-border text-[11px] text-zinc-300 font-mono"
                              >
                                <Camera className="w-3.5 h-3.5 text-brand-orange" />
                                <span>{art.artifact_type}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
