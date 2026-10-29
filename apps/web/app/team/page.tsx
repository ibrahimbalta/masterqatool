'use client';

import React, { useEffect, useState } from 'react';
import { Users, UserPlus, Shield, Trash2, Mail, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api, TeamMember } from '@/lib/api';

export default function TeamWorkspacePage() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [orgId, setOrgId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [inviting, setInviting] = useState(false);

  // Invite form
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('member');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    // Fetch organization info from usage or projects
    api.getProjects().then((projs) => {
      if (projs.length > 0) {
        // Fetch runs or usage to get orgId
        api.getUsage().then(() => {
          // Fallback to fetch orgs directly
          fetch(`${api.getBaseUrl()}/organizations`, {
            headers: { Authorization: `Bearer ${api.getToken()}` },
          })
            .then((r) => r.json())
            .then((orgs) => {
              if (orgs.length > 0) {
                setOrgId(orgs[0].id);
                loadMembers(orgs[0].id);
              } else {
                setLoading(false);
              }
            })
            .catch(() => setLoading(false));
        });
      } else {
        setLoading(false);
      }
    });
  }, []);

  const loadMembers = async (targetOrgId: string) => {
    setLoading(true);
    try {
      const data = await api.getTeamMembers(targetOrgId);
      setMembers(data);
    } catch {
      setMembers([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !orgId) return;
    setSubmitting(true);
    setMessage(null);
    try {
      const newMember = await api.addTeamMember(orgId, email, role);
      setMembers([...members, newMember]);
      setInviting(false);
      setEmail('');
      setMessage(`Invited ${email} with role '${role}'!`);
    } catch (err: any) {
      alert(err.message || 'Failed to add member');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = async (member: TeamMember) => {
    if (!confirm(`Are you sure you want to remove ${member.email}?`)) return;
    try {
      await api.removeTeamMember(orgId, member.id);
      setMembers(members.filter((m) => m.id !== member.id));
    } catch (err: any) {
      alert(err.message || 'Failed to remove member');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Users className="w-6 h-6 text-brand-orange" />
            Team & Workspace
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Manage organization teammates, access control, and test automation permissions.
          </p>
        </div>

        <button
          onClick={() => setInviting(true)}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-brand-orange hover:bg-brand-orangeHover text-white text-xs font-semibold shadow-md transition-all"
        >
          <UserPlus className="w-4 h-4" />
          Invite Teammate
        </button>
      </div>

      {message && (
        <div className="p-3.5 rounded-lg bg-surface-200 border border-brand-orange/30 flex items-center justify-between text-xs text-zinc-200">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-brand-orange" />
            <span>{message}</span>
          </div>
          <button onClick={() => setMessage(null)} className="text-zinc-400 hover:text-white">
            Dismiss
          </button>
        </div>
      )}

      {/* Invite Modal */}
      {inviting && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-300 border border-border rounded-xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-brand-orange" />
              Invite Teammate
            </h2>

            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="colleague@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white placeholder-zinc-500 outline-none focus:border-brand-orange"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-surface-200 border border-border rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-brand-orange"
                >
                  <option value="admin">Admin (Manage tests, projects, and users)</option>
                  <option value="member">Member (Create and execute tests)</option>
                  <option value="viewer">Viewer (Read-only access)</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setInviting(false)}
                  className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-zinc-400 hover:text-white hover:bg-surface-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-brand-orange hover:bg-brand-orangeHover text-white shadow"
                >
                  {submitting ? 'Inviting...' : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Team Members List */}
      <div className="bg-surface-300 border border-border rounded-xl overflow-hidden shadow">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <span className="text-xs font-semibold text-zinc-200 uppercase tracking-wider font-mono">
            Active Members ({members.length})
          </span>
          <span className="text-xs text-zinc-400 font-mono">Organization ID: {orgId ? orgId.slice(0, 8) : '...'}</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-16">
            <Loader2 className="w-8 h-8 text-brand-orange animate-spin" />
          </div>
        ) : members.length === 0 ? (
          <div className="p-12 text-center text-zinc-400 text-xs">
            No members loaded. Connect your organization workspace.
          </div>
        ) : (
          <div className="divide-y divide-border/60">
            {members.map((m) => (
              <div key={m.id} className="p-4 flex items-center justify-between hover:bg-surface-200/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-brand-orange/20 border border-brand-orange/40 text-brand-orange flex items-center justify-center font-semibold text-xs uppercase">
                    {m.email.slice(0, 2)}
                  </div>
                  <div>
                    <p className="text-xs font-medium text-white">{m.full_name || m.email.split('@')[0]}</p>
                    <p className="text-[11px] text-zinc-400 flex items-center gap-1">
                      <Mail className="w-3 h-3" />
                      {m.email}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <span
                    className={`px-2.5 py-1 rounded text-[10px] font-mono uppercase font-semibold border ${
                      m.role === 'owner'
                        ? 'bg-purple-950/40 text-purple-300 border-purple-800/40'
                        : m.role === 'admin'
                        ? 'bg-brand-orange/10 text-brand-orange border-brand-orange/30'
                        : 'bg-surface-200 text-zinc-300 border-border'
                    }`}
                  >
                    {m.role}
                  </span>

                  {m.role !== 'owner' && (
                    <button
                      onClick={() => handleRemove(m)}
                      className="text-zinc-500 hover:text-red-400 p-1.5 transition-colors"
                      title="Remove Member"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Role Permissions Matrix */}
      <div className="bg-surface-300 border border-border rounded-xl p-5 space-y-3">
        <h3 className="text-xs font-semibold text-white uppercase tracking-wider font-mono flex items-center gap-2">
          <Shield className="w-4 h-4 text-brand-orange" />
          Role Permission Hierarchy
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-zinc-400">
          <div className="p-3 rounded-lg bg-surface-200 border border-border">
            <span className="font-semibold text-white block mb-1">Owner</span>
            Workspace control, billing tier changes, member deletion, full runner trigger access.
          </div>
          <div className="p-3 rounded-lg bg-surface-200 border border-border">
            <span className="font-semibold text-brand-orange block mb-1">Admin</span>
            Project creation, test scenario approval, suite management, webhook configuration.
          </div>
          <div className="p-3 rounded-lg bg-surface-200 border border-border">
            <span className="font-semibold text-zinc-300 block mb-1">Member</span>
            Author test scenarios, trigger manual test runs, view evidence & bug dossiers.
          </div>
        </div>
      </div>
    </div>
  );
}
