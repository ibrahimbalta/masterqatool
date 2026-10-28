'use client';

import React, { useEffect, useState } from 'react';
import { FileCheck2, Download, Plus, Check, Clock, Layers, Filter, Loader2 } from 'lucide-react';
import { api, TestCase, Project } from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';

const CATEGORIES = [
  'All',
  'Functional',
  'Negative',
  'Boundary Value',
  'Validation',
  'Regression',
  'Smoke',
  'API',
  'Accessibility',
  'Visual',
  'Exploratory',
];

export default function TestCaseStudioPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
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
      loadCases(selectedProjectId);
    } else {
      setLoading(false);
    }
  }, [selectedProjectId]);

  const loadCases = async (projId: string) => {
    setLoading(true);
    try {
      const data = await api.getTestCases(projId);
      setTestCases(data);
    } catch {
      setTestCases([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredCases = testCases.filter((tc) => {
    if (selectedCategory === 'All') return true;
    return tc.category.toLowerCase() === selectedCategory.toLowerCase();
  });

  const handleApprove = async (caseId: string) => {
    try {
      const updated = await api.updateTestCase(caseId, { approval_status: 'approved' });
      setTestCases((prev) => prev.map((c) => (c.id === caseId ? updated : c)));
    } catch (err: any) {
      alert(err.message || 'Failed to approve test case');
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Test Case Studio</h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Schema-validated manual and automated test specifications with version history.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {selectedProjectId && (
            <a
              href={api.getExportCsvUrl(selectedProjectId)}
              download
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-200 hover:bg-surface-100 border border-border text-xs font-medium text-zinc-200 transition-colors"
            >
              <Download className="w-4 h-4" />
              <span>Export CSV</span>
            </a>
          )}
        </div>
      </div>

      {/* Project Selector & Category Filter */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-surface-200 border border-border">
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-zinc-400">Project:</span>
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

        <div className="flex items-center gap-2 overflow-x-auto">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors whitespace-nowrap ${
                selectedCategory === cat
                  ? 'bg-brand-orange text-white'
                  : 'bg-surface-300 text-zinc-400 hover:text-white border border-border'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex justify-center p-12">
          <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
        </div>
      )}

      {!loading && filteredCases.length === 0 && (
        <div className="p-12 text-center border border-dashed border-border rounded-xl bg-surface-300 space-y-3">
          <FileCheck2 className="w-10 h-10 mx-auto text-zinc-600" />
          <h3 className="text-sm font-semibold text-white">No test cases in this view</h3>
          <p className="text-xs text-zinc-500 max-w-md mx-auto">
            {selectedCategory !== 'All'
              ? `No test cases found matching category '${selectedCategory}'.`
              : 'Test cases generated by AI discovery or manual creation will appear here.'}
          </p>
        </div>
      )}

      {/* Test Case Cards List */}
      <div className="space-y-3">
        {filteredCases.map((tc) => (
          <div
            key={tc.id}
            className="p-5 rounded-xl bg-surface-200 border border-border hover:border-brand-orange/30 transition-all space-y-3"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <span className="px-2 py-0.5 rounded bg-surface-100 border border-border font-mono text-xs font-bold text-brand-orange">
                  {tc.code_identifier}
                </span>
                <h3 className="text-sm font-semibold text-white">{tc.title}</h3>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={tc.approval_status} />
                <span className="text-[11px] font-mono text-zinc-500">v{tc.current_version}</span>
              </div>
            </div>

            {tc.objective && <p className="text-xs text-zinc-400">{tc.objective}</p>}

            {/* Steps & Expected Result Accordion preview */}
            <div className="p-3 rounded-lg bg-surface-300 border border-border text-xs space-y-2">
              <div className="flex items-center justify-between text-zinc-400 text-[11px]">
                <span className="font-semibold text-zinc-300">
                  Steps ({tc.latest_spec?.steps?.length || 0})
                </span>
                <span>Expected: {tc.latest_spec?.expected_result || 'None'}</span>
              </div>

              {tc.latest_spec?.steps && (
                <div className="space-y-1 font-mono text-[11px]">
                  {tc.latest_spec.steps.map((s, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-zinc-400">
                      <span className="text-zinc-600 font-bold">{s.step_number}.</span>
                      <span className="text-brand-orange uppercase text-[10px] px-1 rounded bg-brand-orange/10">
                        {s.action_type}
                      </span>
                      <span>{s.target_locator || s.input_value || 'Direct action'}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-2 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3 text-zinc-500 text-[11px]">
                <span>Category: <strong className="text-zinc-300">{tc.category}</strong></span>
                <span>Priority: <strong className="text-zinc-300 uppercase">{tc.priority}</strong></span>
                <span>Risk: <strong className="text-zinc-300 uppercase">{tc.risk_level}</strong></span>
              </div>

              {tc.approval_status !== 'approved' && (
                <button
                  onClick={() => handleApprove(tc.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/30 text-teal-400 text-xs font-medium transition-colors"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Approve Scenario</span>
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
