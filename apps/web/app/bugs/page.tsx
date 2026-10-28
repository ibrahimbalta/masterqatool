'use client';

import React, { useEffect, useState } from 'react';
import { Bug, AlertCircle, ShieldAlert, CheckCircle2, ChevronRight, Loader2 } from 'lucide-react';
import { api, Bug as BugType } from '@/lib/api';

export default function BugIntelligencePage() {
  const [bugs, setBugs] = useState<BugType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getBugs().then((data) => {
      setBugs(data);
      setLoading(false);
    }).catch(() => {
      setBugs([]);
      setLoading(false);
    });
  }, []);

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

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Bug Intelligence & Triage</h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Automated bug dossiers with reproduction steps, hypothesized root causes, and verification flags.
          </p>
        </div>
      </div>

      {loading && (
        <div className="flex justify-center p-12">
          <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
        </div>
      )}

      {!loading && bugs.length === 0 && (
        <div className="p-12 text-center border border-dashed border-border rounded-xl bg-surface-300 space-y-3">
          <Bug className="w-10 h-10 mx-auto text-zinc-600" />
          <h3 className="text-sm font-semibold text-white">No active bugs detected</h3>
          <p className="text-xs text-zinc-500 max-w-md mx-auto">
            When automated test assertions fail, AI Bug Intelligence extracts DOM snapshots, isolates root causes, and creates actionable reports.
          </p>
        </div>
      )}

      <div className="space-y-4">
        {bugs.map((bug) => (
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
              <span className="text-[11px] font-mono uppercase px-2 py-0.5 rounded bg-surface-100 text-zinc-400 border border-border">
                Status: {bug.status}
              </span>
            </div>

            {bug.description && <p className="text-xs text-zinc-400">{bug.description}</p>}

            {/* Expected vs Actual */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-lg bg-surface-300 border border-border space-y-1">
                <span className="text-[10px] uppercase font-bold text-emerald-400 block">Expected Behavior</span>
                <p className="text-zinc-300">{bug.expected_behavior || 'Not specified'}</p>
              </div>
              <div className="p-3 rounded-lg bg-surface-300 border border-border space-y-1">
                <span className="text-[10px] uppercase font-bold text-red-400 block">Actual Behavior</span>
                <p className="text-zinc-300">{bug.actual_behavior || 'Not specified'}</p>
              </div>
            </div>

            {/* Root cause hypothesis vs verified cause */}
            <div className="p-3 rounded-lg bg-surface-300 border border-border text-xs space-y-1.5">
              <div className="flex items-center gap-2 text-zinc-400">
                <ShieldAlert className="w-4 h-4 text-brand-orange shrink-0" />
                <span className="font-semibold text-zinc-300">Hypothesized Root Cause:</span>
              </div>
              <p className="text-zinc-400 text-[11px] pl-6">
                {bug.root_cause_hypothesis || 'Awaiting automated failure investigator analysis...'}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
