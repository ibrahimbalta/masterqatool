'use client';

import React, { useEffect, useState } from 'react';
import { Compass, Play, Globe, CheckCircle2, AlertTriangle, Layers, Code, ShieldCheck, Loader2 } from 'lucide-react';
import { api, Project } from '@/lib/api';

interface DiscoveredPageItem {
  id: string;
  url: string;
  path: string;
  http_status: number;
  title: string;
  forms_detected: Array<{
    form_id: string;
    method: string;
    action: string;
    fields: Array<{
      name: string;
      type: string;
      required: boolean;
      recommended_locator?: string;
    }>;
    buttons: Array<{
      text: string;
      type: string;
    }>;
  }>;
  accessibility_tree: {
    landmarks?: string[];
    buttons_outside_forms?: Array<{ text: string; locator: string }>;
  };
  provenance: string;
  created_at: string;
}

interface ScanItem {
  id: string;
  project_id: string;
  scan_type: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  summary: {
    pages_discovered?: number;
    forms_detected?: number;
  };
  discovered_pages?: DiscoveredPageItem[];
}

export default function ProjectIntelligencePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [scans, setScans] = useState<ScanItem[]>([]);
  const [activeScan, setActiveScan] = useState<ScanItem | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getProjects().then((projs) => {
      setProjects(projs);
      if (projs.length > 0) {
        setSelectedProjectId(projs[0].id);
      } else {
        setLoading(false);
      }
    });
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      loadScans(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadScans = async (projId: string) => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/projects/${projId}/scans`, {
        headers: { Authorization: `Bearer ${api.getToken()}` },
      });
      if (res.ok) {
        const data = await res.json();
        setScans(data);
        if (data.length > 0) {
          // Fetch full scan details including discovered pages
          const detailRes = await fetch(`http://localhost:8000/api/v1/projects/${projId}/scans/${data[0].id}`, {
            headers: { Authorization: `Bearer ${api.getToken()}` },
          });
          if (detailRes.ok) {
            setActiveScan(await detailRes.json());
          }
        } else {
          setActiveScan(null);
        }
      }
    } catch {
      setScans([]);
      setActiveScan(null);
    } finally {
      setLoading(false);
    }
  };

  const handleStartScan = async () => {
    if (!selectedProjectId) return;
    setIsScanning(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/projects/${selectedProjectId}/scans?sync=true`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${api.getToken()}`,
        },
        body: JSON.stringify({ scan_type: 'url_crawler', max_pages: 10 }),
      });
      if (res.ok) {
        const fullScan = await res.json();
        setScans((prev) => [fullScan, ...prev]);
        setActiveScan(fullScan);
      } else {
        const err = await res.json();
        alert(err.detail || 'Discovery scan failed');
      }
    } catch (e: any) {
      alert(e.message || 'Error starting scan');
    } finally {
      setIsScanning(false);
    }
  };

  const getProvenanceBadge = (provenance: string) => {
    switch (provenance.toLowerCase()) {
      case 'observed':
        return { label: 'GÖZLEMLENDİ', style: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
      case 'source_code':
        return { label: 'KAYNAK KODUNDAN BULUNDU', style: 'bg-blue-500/10 text-blue-400 border-blue-500/30' };
      case 'ai_inferred':
        return { label: 'AI ÇIKARIMI', style: 'bg-purple-500/10 text-purple-400 border-purple-500/30' };
      default:
        return { label: 'DOĞRULANMADI', style: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/30' };
    }
  };

  const pages = activeScan?.discovered_pages || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">Project Intelligence</h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Automated crawler topology, discovered accessible forms, technical surface analysis, and provenance mapping.
          </p>
        </div>
        <button
          onClick={handleStartScan}
          disabled={isScanning || !selectedProjectId}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-medium shadow-md shadow-brand-orange/20 disabled:opacity-50 transition-all"
        >
          {isScanning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
          <span>Run Live Web Discovery</span>
        </button>
      </div>

      {/* Project Selector Bar */}
      <div className="flex items-center gap-3 p-4 rounded-xl bg-surface-200 border border-border">
        <span className="text-xs font-medium text-zinc-400">Target Project:</span>
        <select
          value={selectedProjectId}
          onChange={(e) => setSelectedProjectId(e.target.value)}
          className="px-3 py-1.5 rounded-lg bg-surface-300 border border-border text-xs text-white focus:outline-none focus:border-brand-orange"
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name} ({p.environment}) — {p.target_url}
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="flex justify-center p-12">
          <Loader2 className="w-6 h-6 animate-spin text-brand-orange" />
        </div>
      )}

      {!loading && !activeScan && (
        <div className="p-12 text-center border border-dashed border-border rounded-xl bg-surface-300 space-y-3">
          <Compass className="w-10 h-10 mx-auto text-zinc-600" />
          <h3 className="text-sm font-semibold text-white">No discovery crawl on record</h3>
          <p className="text-xs text-zinc-500 max-w-md mx-auto">
            Click &quot;Run Live Web Discovery&quot; to inspect HTML structure, detect accessible forms, extract inputs, and catalog user flows.
          </p>
          <button
            onClick={handleStartScan}
            disabled={isScanning}
            className="px-4 py-2 rounded-lg bg-brand-orange text-white text-xs font-medium mt-2"
          >
            Start Discovery Crawl
          </button>
        </div>
      )}

      {/* Discovered Surface Details */}
      {!loading && activeScan && (
        <div className="space-y-6">
          {/* Metrics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-surface-200 border border-border">
              <span className="text-[11px] text-zinc-400 block font-mono">DISCOVERED PAGES</span>
              <span className="text-2xl font-bold text-white font-mono mt-1 block">
                {activeScan.summary?.pages_discovered ?? pages.length}
              </span>
            </div>
            <div className="p-4 rounded-xl bg-surface-200 border border-border">
              <span className="text-[11px] text-zinc-400 block font-mono">INTERACTIVE FORMS</span>
              <span className="text-2xl font-bold text-brand-orange font-mono mt-1 block">
                {activeScan.summary?.forms_detected ?? 0}
              </span>
            </div>
            <div className="p-4 rounded-xl bg-surface-200 border border-border">
              <span className="text-[11px] text-zinc-400 block font-mono">SCAN TYPE</span>
              <span className="text-sm font-bold text-zinc-200 uppercase font-mono mt-2 block">
                {activeScan.scan_type}
              </span>
            </div>
            <div className="p-4 rounded-xl bg-surface-200 border border-border">
              <span className="text-[11px] text-zinc-400 block font-mono">LAST CRAWL TIME</span>
              <span className="text-xs text-zinc-300 font-mono mt-2 block">
                {activeScan.completed_at ? new Date(activeScan.completed_at).toLocaleTimeString() : 'In Progress'}
              </span>
            </div>
          </div>

          {/* Discovered Pages and Form Elements */}
          <div className="space-y-4">
            <h2 className="text-sm font-semibold text-white tracking-wide uppercase font-mono">
              Crawled Pages & Elements ({pages.length})
            </h2>

            {pages.map((p) => {
              const prov = getProvenanceBadge(p.provenance);
              return (
                <div
                  key={p.id}
                  className="p-5 rounded-xl bg-surface-200 border border-border hover:border-brand-orange/30 transition-all space-y-4"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <span className="px-2 py-0.5 rounded bg-surface-100 text-zinc-300 text-xs font-mono font-bold">
                        HTTP {p.http_status || 200}
                      </span>
                      <h3 className="text-sm font-bold text-white">{p.title || p.path}</h3>
                    </div>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${prov.style}`}>
                      {prov.label}
                    </span>
                  </div>

                  <div className="text-xs font-mono text-zinc-400 flex items-center gap-2">
                    <Globe className="w-3.5 h-3.5 text-zinc-500" />
                    <span className="text-zinc-300">{p.url}</span>
                  </div>

                  {/* Forms Breakdown */}
                  {Array.isArray(p.forms_detected) && p.forms_detected.length > 0 && (
                    <div className="p-4 rounded-lg bg-surface-300 border border-border space-y-3">
                      <span className="text-xs font-semibold text-zinc-300 block">
                        Detected Forms ({p.forms_detected.length})
                      </span>
                      {p.forms_detected.map((form: any, fIdx: number) => {
                        const formFields: any[] = form.fields || form.inputs || [];
                        return (
                          <div key={fIdx} className="space-y-2 text-xs font-mono">
                            <div className="flex items-center gap-2 text-zinc-400">
                              <span className="text-brand-orange uppercase">{form.method || 'POST'}</span>
                              <span>{form.action || 'Default Action'}</span>
                              <span className="text-zinc-600">ID: {form.form_id || `form_${fIdx}`}</span>
                            </div>

                            {formFields.length > 0 && (
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                                {formFields.map((f: any, fieldIdx: number) => (
                                  <div
                                    key={fieldIdx}
                                    className="p-2 rounded bg-surface-200 border border-border flex items-center justify-between text-[11px]"
                                  >
                                    <div>
                                      <span className="text-white font-semibold">{f.name || 'unnamed'}</span>
                                      <span className="text-zinc-500 ml-1.5">({f.type || 'text'})</span>
                                    </div>
                                    <span className="text-brand-orange text-[10px] truncate max-w-[140px]">
                                      {f.recommended_locator || `[name="${f.name || ''}"]`}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
