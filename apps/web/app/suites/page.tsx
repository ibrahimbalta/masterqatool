'use client';

import React, { useEffect, useState } from 'react';
import { Layers, Plus, Play, CheckCircle2, FolderKanban, Loader2, AlertCircle } from 'lucide-react';
import { api, Project, TestSuite, TestCase } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';

export default function TestSuitesPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [creatingSuite, setCreatingSuite] = useState(false);
  const [selectedSuite, setSelectedSuite] = useState<TestSuite | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('smoke');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [executingSuiteId, setExecutingSuiteId] = useState<string | null>(null);
  const [executionMessage, setExecutionMessage] = useState<string | null>(null);

  useEffect(() => {
    api.getProjects().then((projs) => {
      setProjects(projs);
      if (projs.length > 0) {
        const urlParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
        const targetProjId = urlParams?.get('projectId');
        if (targetProjId && projs.some((p) => p.id === targetProjId)) {
          setSelectedProjectId(targetProjId);
        } else {
          const seramikProj = projs.find((p) => p.name.toLowerCase().includes('seramik') || p.target_url.includes('seramikbak'));
          setSelectedProjectId(seramikProj ? seramikProj.id : projs[0].id);
        }
      }
    });
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadData(selectedProjectId);
    } else {
      setLoading(false);
    }
  }, [selectedProjectId]);

  const loadData = async (projId: string) => {
    setLoading(true);
    try {
      const [suitesData, casesData] = await Promise.all([
        api.getTestSuites(projId),
        api.getTestCases(projId),
      ]);
      setSuites(suitesData);
      setTestCases(casesData);
    } catch {
      setSuites([]);
      setTestCases([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSuite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !selectedProjectId) return;
    setIsSubmitting(true);
    try {
      const created = await api.createTestSuite(selectedProjectId, {
        name,
        description,
        category,
      });
      setSuites([created, ...suites]);
      setCreatingSuite(false);
      setName('');
      setDescription('');
    } catch (err: any) {
      alert(err.message || 'Failed to create suite');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunSuite = async (suite: TestSuite) => {
    setExecutingSuiteId(suite.id);
    setExecutionMessage(null);
    try {
      const fullSuite = await api.getTestSuite(suite.id);
      const caseIds = (fullSuite.test_cases || []).map((c) => c.id);
      if (caseIds.length === 0) {
        setExecutionMessage(`Suite '${suite.name}' has no test cases assigned yet.`);
        return;
      }
      await api.triggerTestRun(selectedProjectId, caseIds);
      setExecutionMessage(`Queued test run for ${caseIds.length} scenario(s) in suite '${suite.name}'!`);
    } catch (err: any) {
      setExecutionMessage(`Failed to trigger suite run: ${err.message}`);
    } finally {
      setExecutingSuiteId(null);
    }
  };

  const handleAssignCases = async (suiteId: string, caseIds: string[]) => {
    try {
      const updated = await api.assignCasesToSuite(suiteId, caseIds);
      setSuites(suites.map((s) => (s.id === updated.id ? updated : s)));
      if (selectedSuite && selectedSuite.id === updated.id) {
        setSelectedSuite(updated);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to assign cases');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Layers className="w-6 h-6 text-brand-orange" />
            Test Suites
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Organize test scenarios into targeted suites for Smoke, Regression, and CI/CD pipelines.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="bg-surface-200 border border-border text-zinc-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-brand-orange"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => setCreatingSuite(true)}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-semibold shadow-md transition-all"
          >
            <Plus className="w-4 h-4" />
            New Suite
          </button>
        </div>
      </div>

      {/* Execution feedback banner */}
      {executionMessage && (
        <div className="p-3.5 rounded-lg bg-surface-200 border border-brand-orange/30 flex items-center justify-between text-xs text-zinc-200">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-brand-orange" />
            <span>{executionMessage}</span>
          </div>
          <button onClick={() => setExecutionMessage(null)} className="text-zinc-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Create Suite Modal */}
      {creatingSuite && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-300 border border-border rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-brand-orange" />
              Create Test Suite
            </h2>

            <form onSubmit={handleCreateSuite} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Suite Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Daily Smoke Verification"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-brand-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-brand-orange"
                >
                  <option value="smoke">Smoke Suite</option>
                  <option value="regression">Regression Suite</option>
                  <option value="critical_path">Critical Path</option>
                  <option value="security">Security & SSRF</option>
                  <option value="performance">Performance & Load</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Description</label>
                <textarea
                  rows={3}
                  placeholder="Brief description of when this suite should be run..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-brand-orange"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setCreatingSuite(false)}
                  className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-white hover:bg-surface-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-brand-orange hover:bg-brand-orangeHover text-white shadow"
                >
                  {isSubmitting ? 'Creating...' : 'Create Suite'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Main Content */}
      {loading ? (
        <div className="flex items-center justify-center p-16">
          <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
        </div>
      ) : suites.length === 0 ? (
        <div className="bg-surface-300 border border-border rounded-xl p-12 text-center max-w-lg mx-auto space-y-4">
          <div className="w-12 h-12 rounded-full bg-brand-orange/10 border border-brand-orange/20 flex items-center justify-center mx-auto text-brand-orange">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">No Test Suites Yet</h3>
            <p className="text-xs text-zinc-400 mt-1">
              Group your individual test scenarios into targeted suites to execute smoke, regression, or full test passes.
            </p>
          </div>
          <button
            onClick={() => setCreatingSuite(true)}
            className="px-4 py-2 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-semibold shadow transition-all inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Create First Suite
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {suites.map((s) => (
            <div
              key={s.id}
              className="bg-surface-300 border border-border hover:border-brand-orange/40 rounded-xl p-5 flex flex-col justify-between transition-all group"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-sm text-white group-hover:text-brand-orange transition-colors">
                    {s.name}
                  </h3>
                  <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono font-medium bg-surface-200 border border-border text-zinc-300">
                    {s.category}
                  </span>
                </div>

                <p className="text-xs text-zinc-400 line-clamp-2">
                  {s.description || 'No description provided.'}
                </p>

                <div className="flex items-center gap-4 text-xs text-zinc-400 font-mono pt-2 border-t border-border/50">
                  <span>{s.total_cases} Scenarios</span>
                  <span>Created {new Date(s.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="pt-4 mt-3 flex items-center justify-between border-t border-border/40 gap-2">
                <button
                  onClick={() => api.getTestSuite(s.id).then(setSelectedSuite)}
                  className="text-xs text-zinc-300 hover:text-white font-medium"
                >
                  Manage Cases →
                </button>

                <button
                  onClick={() => handleRunSuite(s)}
                  disabled={executingSuiteId === s.id}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-200 hover:bg-brand-orange/20 text-zinc-200 hover:text-brand-orange border border-border hover:border-brand-orange/40 text-xs font-medium transition-all"
                >
                  {executingSuiteId === s.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Play className="w-3.5 h-3.5 fill-current" />
                  )}
                  Run Suite
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Suite Detail / Assign Modal */}
      {selectedSuite && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-300 border border-border rounded-xl p-6 max-w-2xl w-full shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div>
                <h2 className="text-base font-semibold text-white flex items-center gap-2">
                  <Layers className="w-5 h-5 text-brand-orange" />
                  {selectedSuite.name}
                </h2>
                <span className="text-xs text-zinc-400">
                  Select scenarios to attach to this suite.
                </span>
              </div>
              <button
                onClick={() => setSelectedSuite(null)}
                className="text-zinc-400 hover:text-white text-xs px-2 py-1"
              >
                Close
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 py-2">
              {testCases.map((tc) => {
                const isAssigned = (selectedSuite.test_cases || []).some((c) => c.id === tc.id);
                return (
                  <div
                    key={tc.id}
                    onClick={() => {
                      const currentIds = (selectedSuite.test_cases || []).map((c) => c.id);
                      const nextIds = isAssigned
                        ? currentIds.filter((id) => id !== tc.id)
                        : [...currentIds, tc.id];
                      handleAssignCases(selectedSuite.id, nextIds);
                    }}
                    className={`flex items-center justify-between p-3 rounded-lg border text-xs cursor-pointer transition-all ${
                      isAssigned
                        ? 'bg-brand-orange/10 border-brand-orange/40 text-white'
                        : 'bg-surface-200 border-border text-zinc-300 hover:bg-surface-100'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center ${
                          isAssigned ? 'bg-brand-orange border-brand-orange text-white' : 'border-zinc-500'
                        }`}
                      >
                        {isAssigned && <CheckCircle2 className="w-3.5 h-3.5" />}
                      </div>
                      <div>
                        <span className="font-mono text-zinc-400 mr-2">{tc.code_identifier}</span>
                        <span className="font-medium text-white">{tc.title}</span>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-mono bg-surface-300 border border-border text-zinc-400">
                      {tc.category}
                    </span>
                  </div>
                );
              })}
            </div>

            <div className="pt-3 border-t border-border flex justify-end">
              <button
                onClick={() => setSelectedSuite(null)}
                className="px-4 py-2 rounded-lg bg-surface-200 hover:bg-surface-100 text-white text-xs font-semibold"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
