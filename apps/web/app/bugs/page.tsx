'use client';

import React, { useEffect, useState } from 'react';
import { Bug, AlertCircle, ShieldAlert, CheckCircle2, ChevronRight, Loader2, Check, Filter, Wrench } from 'lucide-react';
import { api, Bug as BugType, Project } from '@/lib/api';

export default function BugIntelligencePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [bugs, setBugs] = useState<BugType[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    api.getProjects().then((projs) => {
      setProjects(projs);
      if (projs.length > 0) {
        setSelectedProjectId(projs[0].id);
      }
    });
  }, []);

  useEffect(() => {
    loadBugs(selectedProjectId || undefined);
  }, [selectedProjectId]);

  const loadBugs = async (projId?: string) => {
    setLoading(true);
    try {
      const data = await api.getBugs(projId);
      setBugs(data);
    } catch {
      setBugs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (bugId: string, status: string, verifiedCause?: string) => {
    setUpdatingId(bugId);
    try {
      const updated = await api.updateBug(bugId, {
        status,
        verified_cause: verifiedCause,
      });
      setBugs((prev) => prev.map((b) => (b.id === bugId ? updated : b)));
    } catch (err: any) {
      alert(err.message || 'Failed to update bug status');
    } finally {
      setUpdatingId(null);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      case 'high':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'medium':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default:
        return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30';
    }
  };

  const filteredBugs = bugs.filter((b) => {
    if (statusFilter === 'all') return true;
    return b.status.toLowerCase() === statusFilter.toLowerCase();
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Bug className="w-6 h-6 text-brand-orange" />
            Bug Intelligence & Triage
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Automated bug dossiers with reproduction steps, hypothesized root causes, and verification flags.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-surface-200 border border-border text-xs text-white outline-none focus:border-brand-orange"
          >
            <option value="">All Projects</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-surface-200 border border-border text-xs text-white outline-none focus:border-brand-orange"
          >
            <option value="all">All Statuses</option>
            <option value="open">Open</option>
            <option value="verified">Verified</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {loading && (
        <div className="flex justify-center p-12">
          <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
        </div>
      )}

      {!loading && filteredBugs.length === 0 && (
        <div className="p-12 text-center border border-dashed border-border rounded-xl bg-surface-300 space-y-3">
          <Bug className="w-10 h-10 mx-auto text-zinc-600" />
          <h3 className="text-sm font-semibold text-white">No active bugs found</h3>
          <p className="text-xs text-zinc-500 max-w-md mx-auto">
            When automated test assertions fail, AI Bug Intelligence extracts DOM snapshots, isolates root causes, and creates actionable dossiers.
          </p>
        </div>
      )}

      <div className="space-y-4">
        {filteredBugs.map((bug) => (
          <div
            key={bug.id}
            className="p-5 rounded-xl bg-surface-200 border border-border hover:border-brand-orange/30 transition-all space-y-4"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold uppercase border ${getSeverityBadge(bug.severity)}`}>
                  {bug.severity}
                </span>
                <h3 className="text-sm font-semibold text-white">{bug.title}</h3>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono uppercase px-2.5 py-0.5 rounded bg-surface-100 text-zinc-300 border border-border">
                  Status: {bug.status}
                </span>

                {bug.status !== 'resolved' && (
                  <button
                    onClick={() => handleUpdateStatus(bug.id, 'resolved', 'Fix confirmed via test execution')}
                    disabled={updatingId === bug.id}
                    className="flex items-center gap-1 px-2.5 py-1 rounded bg-status-passed/20 hover:bg-status-passed/30 text-status-passed border border-status-passed/30 text-[11px] font-semibold transition-all"
                  >
                    <Check className="w-3.5 h-3.5" />
                    Resolve
                  </button>
                )}

                {bug.status === 'open' && (
                  <button
                    onClick={() => handleUpdateStatus(bug.id, 'verified', 'Confirmed application logic error')}
                    disabled={updatingId === bug.id}
                    className="flex items-center gap-1 px-2.5 py-1 rounded bg-surface-100 hover:bg-surface-50 text-zinc-300 text-[11px] font-medium border border-border transition-all"
                  >
                    Verify Bug
                  </button>
                )}
              </div>
            </div>

            {bug.description && <p className="text-xs text-zinc-400">{bug.description}</p>}

            {/* Reproduction steps */}
            {bug.reproduction_steps && bug.reproduction_steps.length > 0 && (
              <div className="p-3 rounded-lg bg-surface-300 border border-border text-xs space-y-1.5 font-mono">
                <span className="text-[10px] uppercase font-bold text-zinc-400 block font-sans">
                  Reproduction Steps:
                </span>
                {bug.reproduction_steps.map((step, idx) => (
                  <p key={idx} className="text-zinc-300 text-[11px]">
                    {step}
                  </p>
                ))}
              </div>
            )}

            {/* Expected vs Actual */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-lg bg-surface-300 border border-border space-y-1">
                <span className="text-[10px] uppercase font-bold text-emerald-400 block font-sans">Expected Behavior</span>
                <p className="text-zinc-300">{bug.expected_behavior || 'Not specified'}</p>
              </div>
              <div className="p-3 rounded-lg bg-surface-300 border border-border space-y-1">
                <span className="text-[10px] uppercase font-bold text-red-400 block font-sans">Actual Behavior</span>
                <p className="text-zinc-300">{bug.actual_behavior || 'Not specified'}</p>
              </div>
            </div>

            {/* Root cause hypothesis vs verified cause */}
            <div className="p-3 rounded-lg bg-surface-300 border border-border text-xs space-y-1.5">
              <div className="flex items-center gap-2 text-zinc-400">
                <ShieldAlert className="w-4 h-4 text-brand-orange shrink-0" />
                <span className="font-semibold text-zinc-300 font-sans">Hypothesized Root Cause:</span>
              </div>
              <p className="text-zinc-400 text-[11px] pl-6 font-mono">
                {bug.root_cause_hypothesis || 'Awaiting automated failure investigator analysis...'}
              </p>

              {bug.verified_cause && (
                <div className="pt-2 border-t border-border/50 pl-6 text-zinc-300 text-[11px] font-mono">
                  <span className="text-status-passed font-bold font-sans">Verified Cause: </span>
                  {bug.verified_cause}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
