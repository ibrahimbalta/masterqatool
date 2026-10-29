'use client';

import React, { useEffect, useState } from 'react';
import { Cpu, Download, Copy, Check, FileCode, Terminal, ShieldCheck, Loader2 } from 'lucide-react';
import { api, Project, AutomationCode } from '@/lib/api';

export default function AutomationLabPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [automationCode, setAutomationCode] = useState<AutomationCode | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

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
      loadCode(selectedProjectId);
    } else {
      setLoading(false);
    }
  }, [selectedProjectId]);

  const loadCode = async (projId: string) => {
    setLoading(true);
    try {
      const data = await api.getAutomationCode(projId);
      setAutomationCode(data);
    } catch {
      setAutomationCode(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (automationCode?.code) {
      navigator.clipboard.writeText(automationCode.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Cpu className="w-6 h-6 text-brand-orange" />
            Automation Lab
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Production-grade Playwright TypeScript scripts compiled from verified scenario models.
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

          <a
            href={selectedProjectId ? api.getExportPackageUrl(selectedProjectId) : '#'}
            download
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-semibold shadow-md transition-all"
          >
            <Download className="w-4 h-4" />
            Download Package (.zip)
          </a>
        </div>
      </div>

      {/* Lab Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-surface-300 border border-border rounded-xl p-4 space-y-1">
          <span className="text-[11px] font-mono text-zinc-400 uppercase">Automation Framework</span>
          <p className="text-base font-semibold text-white flex items-center gap-2">
            Playwright Test
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-200 text-brand-orange font-mono">v1.44+</span>
          </p>
        </div>

        <div className="bg-surface-300 border border-border rounded-xl p-4 space-y-1">
          <span className="text-[11px] font-mono text-zinc-400 uppercase">Language Target</span>
          <p className="text-base font-semibold text-white">TypeScript Strict</p>
        </div>

        <div className="bg-surface-300 border border-border rounded-xl p-4 space-y-1">
          <span className="text-[11px] font-mono text-zinc-400 uppercase">Compiled Scenarios</span>
          <p className="text-base font-semibold text-white">
            {automationCode?.total_test_cases || 0} Test Specs
          </p>
        </div>

        <div className="bg-surface-300 border border-border rounded-xl p-4 space-y-1">
          <span className="text-[11px] font-mono text-zinc-400 uppercase">Verification Rule</span>
          <p className="text-xs text-status-passed font-medium flex items-center gap-1 mt-1">
            <ShieldCheck className="w-4 h-4 text-status-passed" />
            Zero Fake Pass Policy
          </p>
        </div>
      </div>

      {/* Code Editor Preview Window */}
      <div className="bg-surface-400 border border-border rounded-xl overflow-hidden shadow-2xl">
        {/* Editor Title Bar */}
        <div className="bg-surface-300 border-b border-border px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <div className="w-3 h-3 rounded-full bg-green-500/80" />
            </div>
            <span className="text-xs font-mono text-zinc-400 flex items-center gap-1.5 pl-2 border-l border-border">
              <FileCode className="w-3.5 h-3.5 text-brand-orange" />
              tests/e2e.spec.ts
            </span>
          </div>

          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-200 hover:bg-surface-100 text-zinc-300 hover:text-white text-xs font-medium border border-border transition-all"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-status-passed" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                Copy Code
              </>
            )}
          </button>
        </div>

        {/* Code Content */}
        {loading ? (
          <div className="flex items-center justify-center p-20">
            <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
          </div>
        ) : !automationCode || !automationCode.code ? (
          <div className="p-16 text-center text-zinc-400 text-xs">
            No test scenarios available to compile for this project.
          </div>
        ) : (
          <pre className="p-6 text-xs font-mono text-zinc-200 overflow-x-auto leading-relaxed select-text bg-[#080512]">
            <code>{automationCode.code}</code>
          </pre>
        )}
      </div>

      {/* CI/CD Quickstart Instruction */}
      <div className="bg-surface-300 border border-border rounded-xl p-6 space-y-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <Terminal className="w-4 h-4 text-brand-orange" />
          Local & CI/CD Execution
        </h3>
        <p className="text-xs text-zinc-400 leading-normal">
          Download the test package to run tests in your local development terminal or hook it into GitHub Actions.
        </p>

        <div className="p-3.5 rounded-lg bg-surface-400 border border-border font-mono text-xs text-zinc-300 space-y-1">
          <p className="text-zinc-500"># 1. Unzip the downloaded test package</p>
          <p>unzip playwright-tests.zip && cd playwright-tests</p>
          <p className="text-zinc-500 mt-2"># 2. Install dependencies & headless browser</p>
          <p>npm install && npx playwright install --with-deps</p>
          <p className="text-zinc-500 mt-2"># 3. Run full automated suite with visual HTML report</p>
          <p className="text-brand-orange">npx playwright test</p>
        </div>
      </div>
    </div>
  );
}
