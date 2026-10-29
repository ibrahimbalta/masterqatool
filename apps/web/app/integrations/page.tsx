'use client';

import React, { useEffect, useState } from 'react';
import { Boxes, Github, CheckCircle2, RefreshCw, Key, Globe, Shield, Terminal, Loader2, AlertCircle } from 'lucide-react';
import { api, Project, IntegrationConnection } from '@/lib/api';

export default function IntegrationsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [integrations, setIntegrations] = useState<IntegrationConnection[]>([]);
  const [loading, setLoading] = useState(true);

  // GitHub Form State
  const [repoUrl, setRepoUrl] = useState('');
  const [token, setToken] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [syncResult, setSyncResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    api.getProjects().then((projs) => {
      setProjects(projs);
      if (projs.length > 0) {
        setSelectedProjectId(projs[0].id);
        if (projs[0].github_repo) {
          setRepoUrl(projs[0].github_repo);
        }
      }
    });
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadIntegrations(selectedProjectId);
      const proj = projects.find((p) => p.id === selectedProjectId);
      if (proj && proj.github_repo) {
        setRepoUrl(proj.github_repo);
      }
    } else {
      setLoading(false);
    }
  }, [selectedProjectId]);

  const loadIntegrations = async (projId: string) => {
    setLoading(true);
    try {
      const data = await api.getIntegrations(projId);
      setIntegrations(data);
    } catch {
      setIntegrations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleConnectGitHub = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim() || !selectedProjectId) return;
    setConnecting(true);
    setErrorMsg(null);
    setSyncResult(null);
    try {
      const res = await api.connectGitHub(selectedProjectId, repoUrl, token || undefined);
      setSyncResult(res);
      await loadIntegrations(selectedProjectId);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to connect repository');
    } finally {
      setConnecting(false);
    }
  };

  const githubConn = integrations.find((i) => i.connection_type === 'github');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Boxes className="w-6 h-6 text-brand-orange" />
            Integrations & Connectors
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Connect code repositories, CI/CD pipelines, and webhooks to enrich Project Intelligence.
          </p>
        </div>

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
      </div>

      {/* Integration Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GitHub Integration */}
        <div className="bg-surface-300 border border-border rounded-xl p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-surface-200 border border-border flex items-center justify-center text-white">
                <Github className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">GitHub Repository</h3>
                <p className="text-xs text-zinc-400">Scan source code for routes, manifests, and test files.</p>
              </div>
            </div>

            {githubConn ? (
              <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-status-passed/10 text-status-passed border border-status-passed/20">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Connected
              </span>
            ) : (
              <span className="text-[11px] font-mono text-zinc-500 uppercase">Not Connected</span>
            )}
          </div>

          <form onSubmit={handleConnectGitHub} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">
                Repository URL or Slug
              </label>
              <input
                type="text"
                required
                placeholder="https://github.com/organization/repo or owner/repo"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-brand-orange"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">
                Personal Access Token <span className="text-zinc-500 font-normal">(Optional for public repos)</span>
              </label>
              <input
                type="password"
                placeholder="ghp_xxxxxxxxxxxx"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-brand-orange font-mono"
              />
            </div>

            {errorMsg && (
              <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/40 text-xs text-red-200 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={connecting}
              className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-semibold shadow transition-all"
            >
              {connecting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing Repository...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  Connect & Synchronize
                </>
              )}
            </button>
          </form>

          {/* Sync Result Dossier */}
          {syncResult && (
            <div className="p-4 rounded-lg bg-surface-400 border border-brand-orange/30 space-y-2 text-xs">
              <span className="font-semibold text-brand-orange uppercase text-[10px] tracking-wider font-mono">
                Source Code Discovery Dossier
              </span>
              <p className="text-zinc-300">
                <span className="text-zinc-500">Framework:</span> {syncResult.analysis?.framework_detected}
              </p>
              <p className="text-zinc-300">
                <span className="text-zinc-500">Discovered Routes:</span>{' '}
                {(syncResult.analysis?.detected_routes || []).join(', ')}
              </p>
              <p className="text-zinc-300">
                <span className="text-zinc-500">Existing Test Suites:</span>{' '}
                {(syncResult.analysis?.existing_test_runners || []).join(', ')}
              </p>
            </div>
          )}
        </div>

        {/* Webhook CI/CD Trigger */}
        <div className="bg-surface-300 border border-border rounded-xl p-6 space-y-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-surface-200 border border-border flex items-center justify-center text-white">
              <Terminal className="w-5 h-5 text-brand-orange" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">CI/CD Webhook Trigger</h3>
              <p className="text-xs text-zinc-400">Trigger automated test execution on deploy or pull request.</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">Webhook Endpoint</label>
              <div className="p-2.5 rounded-lg bg-surface-200 border border-border text-xs font-mono text-zinc-300 break-all select-all">
                https://api.masterqa.ai/api/v1/test-runs
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1">cURL Example</label>
              <pre className="p-3 rounded-lg bg-surface-400 border border-border text-[11px] font-mono text-zinc-300 overflow-x-auto leading-relaxed">
{`curl -X POST https://api.masterqa.ai/api/v1/test-runs \\
  -H "Authorization: Bearer <API_TOKEN>" \\
  -H "Content-Type: application/json" \\
  -d '{"project_id": "${selectedProjectId || 'PROJECT_ID'}", "trigger": "ci"}'`}
              </pre>
            </div>

            <div className="p-3 rounded-lg bg-surface-200/50 border border-border text-[11px] text-zinc-400 flex items-start gap-2">
              <Shield className="w-4 h-4 text-brand-orange shrink-0 mt-0.5" />
              <span>
                All incoming CI runs run in the same isolated sandboxes with strict SSRF filtering and step-by-step artifact recording.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
