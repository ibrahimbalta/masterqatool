'use client';

import React, { useState } from 'react';
import { X, CheckCircle, AlertCircle, Loader2, Globe, Github, Shield } from 'lucide-react';
import { api, Project } from '@/lib/api';

interface ProjectWizardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (project: Project) => void;
}

export function ProjectWizardModal({ isOpen, onClose, onCreated }: ProjectWizardModalProps) {
  const [name, setName] = useState('');
  const [targetUrl, setTargetUrl] = useState('');
  const [githubRepo, setGithubRepo] = useState('');
  const [environment, setEnvironment] = useState('staging');
  const [isVerifying, setIsVerifying] = useState(false);
  const [urlVerification, setUrlVerification] = useState<{ verified: boolean; message?: string } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleVerifyUrl = async () => {
    if (!targetUrl) return;
    setIsVerifying(true);
    setUrlVerification(null);
    setError(null);

    try {
      const res = await api.validateUrl(targetUrl);
      if (res.valid) {
        setUrlVerification({ verified: true, message: 'URL and SSRF security check verified successfully.' });
      } else {
        setUrlVerification({ verified: false, message: res.message });
      }
    } catch (err: any) {
      setUrlVerification({ verified: false, message: err.message || 'Verification connection failed' });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlVerification?.verified) {
      setError('You must verify the target URL with the security check before creating the project.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const project = await api.createProject({
        name,
        target_url: targetUrl,
        github_repo: githubRepo || undefined,
        environment,
      });
      onCreated(project);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create project');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-surface-300 border border-border rounded-xl w-full max-w-lg shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-150">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-brand-orange" />
            <h2 className="text-base font-semibold text-white">New QA Automation Project</h2>
          </div>
          <button onClick={onClose} className="text-zinc-400 hover:text-white p-1 rounded-lg">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1.5">Project Name *</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Core Commerce Web App"
              className="w-full px-3 py-2 rounded-lg bg-surface-200 border border-border text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-orange"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1.5">
              Target Web Application URL *
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Globe className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
                <input
                  type="url"
                  required
                  value={targetUrl}
                  onChange={(e) => {
                    setTargetUrl(e.target.value);
                    setUrlVerification(null);
                  }}
                  placeholder="https://staging.myapp.com"
                  className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-200 border border-border text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-orange"
                />
              </div>
              <button
                type="button"
                onClick={handleVerifyUrl}
                disabled={!targetUrl || isVerifying}
                className="px-3 py-2 rounded-lg bg-surface-100 hover:bg-surface-50 border border-border text-xs font-medium text-zinc-200 disabled:opacity-50 flex items-center gap-1.5"
              >
                {isVerifying ? <Loader2 className="w-3.5 h-3.5 animate-spin text-brand-orange" /> : 'Verify'}
              </button>
            </div>

            {urlVerification && (
              <div
                className={`mt-2 p-2 rounded-md border text-[11px] flex items-start gap-2 ${
                  urlVerification.verified
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : 'bg-red-500/10 border-red-500/30 text-red-400'
                }`}
              >
                {urlVerification.verified ? (
                  <CheckCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-emerald-400" />
                ) : (
                  <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-red-400" />
                )}
                <span>{urlVerification.message}</span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1.5">
              GitHub Repository (Optional)
            </label>
            <div className="relative">
              <Github className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={githubRepo}
                onChange={(e) => setGithubRepo(e.target.value)}
                placeholder="e.g. acme-corp/storefront-app"
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-200 border border-border text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-orange"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1.5">Authorized Environment</label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-surface-200 border border-border text-xs text-white focus:outline-none focus:border-brand-orange"
            >
              <option value="staging">Staging (Isolated QA Target)</option>
              <option value="preview">Preview (PR ephemeral deploy)</option>
              <option value="dev">Development Sandbox</option>
              <option value="production">Production (Read-only Synthetic)</option>
            </select>
          </div>

          <div className="pt-3 border-t border-border flex justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-border text-xs text-zinc-400 hover:text-white hover:bg-surface-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !urlVerification?.verified}
              className="px-4 py-2 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-medium shadow-md shadow-brand-orange/20 disabled:opacity-50 transition-all flex items-center gap-1.5"
            >
              {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Create & Ready for Analysis
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
