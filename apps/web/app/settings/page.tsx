'use client';

import React, { useState } from 'react';
import { Settings, Shield, Sliders, Bell, Database, Lock, Save, CheckCircle2 } from 'lucide-react';

export default function SettingsPage() {
  const [workspaceName, setWorkspaceName] = useState('Enterprise Workspace');
  const [allowPrivateDev, setAllowPrivateDev] = useState(false);
  const [stepTimeoutSeconds, setStepTimeoutSeconds] = useState(15);
  const [traceRetentionDays, setTraceRetentionDays] = useState(30);
  const [autoScreenshotOnFail, setAutoScreenshotOnFail] = useState(true);
  const [aiProvider, setAiProvider] = useState('mock');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Settings className="w-6 h-6 text-brand-orange" />
            Platform Settings
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Configure isolated browser sandbox parameters, SSRF security limits, and AI test design providers.
          </p>
        </div>

        {saved && (
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-status-passed/20 text-status-passed border border-status-passed/40 text-xs font-medium">
            <CheckCircle2 className="w-4 h-4" />
            Settings Saved
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Workspace Configuration */}
        <div className="bg-surface-300 border border-border rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-border pb-3">
            <Sliders className="w-4 h-4 text-brand-orange" />
            Workspace Parameters
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Workspace Name</label>
              <input
                type="text"
                value={workspaceName}
                onChange={(e) => setWorkspaceName(e.target.value)}
                className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-brand-orange"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">AI Test Generation Model</label>
              <select
                value={aiProvider}
                onChange={(e) => setAiProvider(e.target.value)}
                className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-brand-orange"
              >
                <option value="mock">Deterministic Schema Mock (Offline Verified)</option>
                <option value="openai">OpenAI GPT-4o (Structured JSON Mode)</option>
                <option value="claude">Anthropic Claude 3.5 Sonnet</option>
              </select>
            </div>
          </div>
        </div>

        {/* Execution & Sandbox Policy */}
        <div className="bg-surface-300 border border-border rounded-xl p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 border-b border-border pb-3">
            <Shield className="w-4 h-4 text-brand-orange" />
            Execution Sandbox & SSRF Defense
          </h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-surface-200 border border-border">
              <div>
                <p className="text-xs font-medium text-white">Strict SSRF Protection</p>
                <p className="text-[11px] text-zinc-400">
                  Blocks 127.0.0.1, RFC1918 private IPs, and cloud metadata (169.254.169.254) on every step.
                </p>
              </div>
              <span className="px-2.5 py-1 rounded text-[10px] uppercase font-mono font-bold bg-status-passed/20 text-status-passed border border-status-passed/30">
                ACTIVE
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-surface-200 border border-border">
              <div>
                <p className="text-xs font-medium text-white">Allow Private Host Testing (Dev mode only)</p>
                <p className="text-[11px] text-zinc-400">
                  Allows authorized testing of internal staging targets behind private corporate VPCs.
                </p>
              </div>
              <input
                type="checkbox"
                checked={allowPrivateDev}
                onChange={(e) => setAllowPrivateDev(e.target.checked)}
                className="w-4 h-4 accent-brand-orange rounded cursor-pointer"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  Step Execution Timeout (seconds)
                </label>
                <input
                  type="number"
                  min="3"
                  max="60"
                  value={stepTimeoutSeconds}
                  onChange={(e) => setStepTimeoutSeconds(Number(e.target.value))}
                  className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-brand-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">
                  Evidence Retention Period (days)
                </label>
                <input
                  type="number"
                  min="7"
                  max="365"
                  value={traceRetentionDays}
                  onChange={(e) => setTraceRetentionDays(Number(e.target.value))}
                  className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-brand-orange"
                />
              </div>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-surface-200 border border-border">
              <div>
                <p className="text-xs font-medium text-white">Automatic Screenshot Capture on Failure</p>
                <p className="text-[11px] text-zinc-400">
                  Takes high-resolution browser viewport screenshots immediately upon assertion or locator failure.
                </p>
              </div>
              <input
                type="checkbox"
                checked={autoScreenshotOnFail}
                onChange={(e) => setAutoScreenshotOnFail(e.target.checked)}
                className="w-4 h-4 accent-brand-orange rounded cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Save Bar */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-semibold shadow-lg transition-all"
          >
            <Save className="w-4 h-4" />
            Save Preferences
          </button>
        </div>
      </form>
    </div>
  );
}
