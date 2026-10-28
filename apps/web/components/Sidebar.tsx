'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  FolderKanban,
  Compass,
  FileCheck2,
  Layers,
  PlaySquare,
  Bug,
  Cpu,
  Boxes,
  Users,
  CreditCard,
  Settings,
  ShieldAlert,
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Project Intelligence', href: '/intelligence', icon: Compass },
  { name: 'Test Case Studio', href: '/test-cases', icon: FileCheck2 },
  { name: 'Test Suites', href: '/suites', icon: Layers },
  { name: 'Execution Center', href: '/execution', icon: PlaySquare },
  { name: 'Bug Intelligence', href: '/bugs', icon: Bug },
  { name: 'Automation Lab', href: '/automation', icon: Cpu },
  { name: 'Integrations', href: '/integrations', icon: Boxes },
  { name: 'Team & Workspace', href: '/team', icon: Users },
  { name: 'Usage & Billing', href: '/usage', icon: CreditCard },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-surface-300 border-r border-border flex flex-col h-screen fixed left-0 top-0 z-30 select-none">
      {/* Brand logo & title */}
      <div className="h-16 flex items-center px-6 border-b border-border gap-3">
        <div className="w-8 h-8 rounded-lg bg-brand-orange flex items-center justify-center font-bold text-white shadow-lg shadow-brand-orange/30">
          QA
        </div>
        <div>
          <span className="font-semibold text-white tracking-tight text-sm">AI QA Agent</span>
          <span className="block text-[10px] text-zinc-400 uppercase tracking-widest font-mono">Enterprise SaaS</span>
        </div>
      </div>

      {/* Navigation list */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="text-[11px] font-semibold text-zinc-500 uppercase px-3 py-1 font-mono tracking-wider">
          Platform
        </div>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                isActive
                  ? 'bg-surface-50 text-brand-orange border border-brand-orange/20 font-semibold'
                  : 'text-zinc-400 hover:text-white hover:bg-surface-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-brand-orange' : 'text-zinc-400'}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Verification notice pill */}
      <div className="p-4 border-t border-border bg-surface-400">
        <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-surface-200/50 border border-border text-[11px] text-zinc-400">
          <ShieldAlert className="w-4 h-4 text-brand-orange shrink-0 mt-0.5" />
          <p className="leading-tight">
            <span className="text-zinc-200 font-medium">True Verification Policy:</span> AI assertions strictly require sandboxed Playwright execution evidence.
          </p>
        </div>
      </div>
    </aside>
  );
}
