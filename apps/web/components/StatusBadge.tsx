import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toLowerCase();

  const getStyle = () => {
    switch (normalized) {
      case 'passed':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'failed':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      case 'running':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30 animate-pulse';
      case 'queued':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'blocked':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'flaky':
        return 'bg-pink-500/10 text-pink-400 border-pink-500/30';
      case 'approved':
        return 'bg-teal-500/10 text-teal-400 border-teal-500/30';
      case 'in_review':
        return 'bg-orange-500/10 text-orange-400 border-orange-500/30';
      case 'cancelled':
      default:
        return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30';
    }
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border font-mono tracking-wide uppercase ${getStyle()}`}>
      {status}
    </span>
  );
}
