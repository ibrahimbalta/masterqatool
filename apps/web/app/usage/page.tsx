'use client';

import React, { useEffect, useState } from 'react';
import { CreditCard, CheckCircle, Shield, Zap, Loader2 } from 'lucide-react';
import { api, UsageSummary } from '@/lib/api';

export default function UsagePage() {
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getUsage().then((data) => {
      setUsage(data);
      setLoading(false);
    }).catch(() => {
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="pb-4 border-b border-border">
        <h1 className="text-xl font-bold text-white tracking-tight">Usage Quotas & SaaS Subscriptions</h1>
        <p className="text-xs text-zinc-400 mt-0.5">
          Auditable resource consumption, plan boundaries, and concurrency limits.
        </p>
      </div>

      {loading && (
        <div className="flex justify-center p-12">
          <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
        </div>
      )}

      {usage && (
        <div className="space-y-6">
          {/* Current Plan Card */}
          <div className="p-6 rounded-xl bg-surface-200 border border-border flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase font-mono tracking-wider text-zinc-400">Current Plan</span>
                <span className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/30 text-brand-orange font-bold font-mono text-xs uppercase">
                  {usage.plan_tier}
                </span>
              </div>
              <h2 className="text-lg font-bold text-white mt-1">Multi-Tenant Organization Workspace</h2>
              <p className="text-xs text-zinc-400 mt-0.5">
                Up to {usage.concurrent_runs_limit} concurrent sandboxed browser run(s) enabled.
              </p>
            </div>
          </div>

          {/* Quota Progress Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Test Minutes */}
            <div className="p-5 rounded-xl bg-surface-200 border border-border space-y-3">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-zinc-400">Execution Minutes</span>
                <span className="font-mono text-white">
                  {usage.test_minutes_used.toFixed(1)} / {usage.test_minutes_limit} min
                </span>
              </div>
              <div className="w-full bg-surface-300 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-brand-orange h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, (usage.test_minutes_used / usage.test_minutes_limit) * 100)}%` }}
                />
              </div>
              <span className="text-[11px] text-zinc-500 block">Resets at the start of each billing cycle</span>
            </div>

            {/* Projects Quota */}
            <div className="p-5 rounded-xl bg-surface-200 border border-border space-y-3">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-zinc-400">Target Projects</span>
                <span className="font-mono text-white">
                  {usage.projects_count} / {usage.projects_limit}
                </span>
              </div>
              <div className="w-full bg-surface-300 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-500 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, (usage.projects_count / usage.projects_limit) * 100)}%` }}
                />
              </div>
              <span className="text-[11px] text-zinc-500 block">Simultaneous active target projects</span>
            </div>

            {/* AI Tokens */}
            <div className="p-5 rounded-xl bg-surface-200 border border-border space-y-3">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-zinc-400">AI Design Tokens</span>
                <span className="font-mono text-white">
                  {usage.ai_tokens_used.toLocaleString()} / {usage.ai_tokens_limit.toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-surface-300 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-purple-500 h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, (usage.ai_tokens_used / usage.ai_tokens_limit) * 100)}%` }}
                />
              </div>
              <span className="text-[11px] text-zinc-500 block">Schema-validated LLM test design queries</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
