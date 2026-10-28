'use client';

import React from 'react';
import { Bell, Terminal, ShieldCheck } from 'lucide-react';

export function Header() {
  return (
    <header className="h-16 border-b border-border bg-surface-300/80 backdrop-blur px-8 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-surface-200 border border-border text-xs text-zinc-300 font-mono">
          <Terminal className="w-3.5 h-3.5 text-brand-orange" />
          <span>API: connected</span>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-400 font-mono">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>SSRF Defense: Active</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="p-2 text-zinc-400 hover:text-white rounded-lg hover:bg-surface-200 transition-colors relative">
          <Bell className="w-4 h-4" />
          <span className="w-2 h-2 rounded-full bg-brand-orange absolute top-1.5 right-1.5" />
        </button>

        <div className="flex items-center gap-3 pl-4 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-brand-orange/20 border border-brand-orange/40 flex items-center justify-center text-xs font-semibold text-brand-orange">
            QA
          </div>
          <div className="text-left">
            <span className="text-xs font-medium text-white block">Lead Architect</span>
            <span className="text-[10px] text-zinc-500 block">Acme QA Corp</span>
          </div>
        </div>
      </div>
    </header>
  );
}
