'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FolderKanban, Plus, Globe, Github, ExternalLink, Play, Search, Loader2 } from 'lucide-react';
import { api, Project } from '@/lib/api';
import { ProjectWizardModal } from '@/components/ProjectWizardModal';

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [runningProjectId, setRunningProjectId] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch {
      setProjects([]);
    } finally {
      setLoading(false);
    }
  };

  const filtered = projects.filter((p) =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.target_url.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Projects & Target Applications</h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Manage web applications, configure environments, and initiate automated discovery.
          </p>
        </div>
        <button
          onClick={() => setIsWizardOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-medium shadow-md shadow-brand-orange/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Project</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by project name or target URL..."
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-200 border border-border text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-brand-orange"
          />
        </div>
      </div>

      {loading && (
        <div className="flex justify-center p-12">
          <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="p-12 text-center border border-dashed border-border rounded-xl bg-surface-300 space-y-3">
          <FolderKanban className="w-10 h-10 mx-auto text-zinc-600" />
          <h3 className="text-sm font-semibold text-white">No projects found</h3>
          <p className="text-xs text-zinc-500 max-w-md mx-auto">
            {searchTerm
              ? 'No projects match your search filter.'
              : 'Add your first target application to begin web crawling and AI test case generation.'}
          </p>
          {!searchTerm && (
            <button
              onClick={() => setIsWizardOpen(true)}
              className="px-4 py-2 rounded-lg bg-brand-orange text-white text-xs font-medium mt-2"
            >
              + Create Project
            </button>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((project) => (
          <div
            key={project.id}
            className="p-5 rounded-xl bg-surface-200 border border-border hover:border-brand-orange/40 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold text-white tracking-tight">{project.name}</h3>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-surface-100 text-zinc-300 border border-border">
                  {project.environment}
                </span>
              </div>
              {project.description && (
                <p className="text-xs text-zinc-400 mt-1.5 line-clamp-2">{project.description}</p>
              )}

              <div className="mt-4 space-y-2 text-xs font-mono">
                <div className="flex items-center gap-2 text-zinc-400">
                  <Globe className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                  <a
                    href={project.target_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="truncate hover:text-brand-orange flex items-center gap-1"
                  >
                    <span>{project.target_url}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>

                {project.github_repo && (
                  <div className="flex items-center gap-2 text-zinc-400">
                    <Github className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                    <span className="truncate">{project.github_repo}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-border flex items-center justify-between">
              <span className="text-[11px] text-zinc-500">
                Created {new Date(project.created_at).toLocaleDateString()}
              </span>
              <button
                disabled={runningProjectId === project.id}
                onClick={async () => {
                  setRunningProjectId(project.id);
                  try {
                    await api.triggerTestRun(project.id);
                    router.push(`/execution?projectId=${project.id}`);
                  } catch (e: any) {
                    alert(e.message || 'Error triggering run');
                    setRunningProjectId(null);
                  }
                }}
                className="px-3 py-1.5 rounded-lg bg-surface-100 hover:bg-surface-50 border border-border text-xs font-medium text-brand-orange flex items-center gap-1.5 transition-colors disabled:opacity-50"
              >
                {runningProjectId === project.id ? (
                  <>
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Starting...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3" />
                    <span>Run Playwright</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      <ProjectWizardModal
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        onCreated={(newProj) => setProjects([newProj, ...projects])}
      />
    </div>
  );
}
