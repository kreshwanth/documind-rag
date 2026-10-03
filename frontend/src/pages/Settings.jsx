import React, { useEffect, useState } from 'react';
import { healthApi } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Settings as SettingsIcon, Shield, Server, Cpu, Database, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export const Settings = () => {
  const { user } = useAuth();
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await healthApi.check();
        setHealth(res.data);
      } catch (err) {
        setHealth({ status: 'unhealthy', database: 'error', vector_extension: 'error' });
      } finally {
        setLoading(false);
      }
    };
    checkHealth();
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">System & Account Settings</h1>
        <p className="text-xs text-slate-400 mt-1">
          Review tenant isolation properties, model hyperparameters, and PostgreSQL pgvector connection status.
        </p>
      </div>

      {/* Account Info */}
      <div className="glass-panel rounded-3xl p-6 space-y-4 shadow-sm">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <Shield className="h-5 w-5 text-brand-400" />
          Enterprise User Profile
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800">
            <span className="text-slate-400">Full Name</span>
            <p className="text-sm font-semibold text-white mt-1">{user?.name}</p>
          </div>
          <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800">
            <span className="text-slate-400">Corporate Email</span>
            <p className="text-sm font-semibold text-white mt-1">{user?.email}</p>
          </div>
          <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800">
            <span className="text-slate-400">User Tenant ID</span>
            <p className="text-xs font-mono text-slate-300 mt-1">{user?.id}</p>
          </div>
          <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800">
            <span className="text-slate-400">Isolation Security Policy</span>
            <p className="text-xs font-semibold text-emerald-400 mt-1">Tenant Scoped (Strict)</p>
          </div>
        </div>
      </div>

      {/* System Health */}
      <div className="glass-panel rounded-3xl p-6 space-y-4 shadow-sm">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <Server className="h-5 w-5 text-brand-400" />
          Infrastructure & pgvector Status
        </h3>

        {loading ? (
          <div className="p-6 text-center text-slate-400">
            <Loader2 className="h-6 w-6 animate-spin mx-auto text-brand-400 mb-2" />
            <span className="text-xs">Checking system health...</span>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-slate-400">FastAPI Gateway</span>
                <p className="text-sm font-semibold text-white capitalize mt-1">{health?.status}</p>
              </div>
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            </div>

            <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-slate-400">PostgreSQL DB</span>
                <p className="text-sm font-semibold text-white capitalize mt-1">{health?.database}</p>
              </div>
              <Database className="h-5 w-5 text-brand-400" />
            </div>

            <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-slate-400">pgvector Extension</span>
                <p className="text-sm font-semibold text-white capitalize mt-1">{health?.vector_extension}</p>
              </div>
              <Cpu className="h-5 w-5 text-purple-400" />
            </div>
          </div>
        )}
      </div>

      {/* Model Specs */}
      <div className="glass-panel rounded-3xl p-6 space-y-4 shadow-sm">
        <h3 className="text-base font-semibold text-white flex items-center gap-2">
          <Cpu className="h-5 w-5 text-brand-400" />
          Configured AI Models & Parameters
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800">
            <span className="text-slate-400">Embedding Model</span>
            <p className="text-sm font-semibold text-white mt-1">Google text-embedding-004 (768-dim)</p>
          </div>
          <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800">
            <span className="text-slate-400">Generative LLM</span>
            <p className="text-sm font-semibold text-white mt-1">Google gemini-1.5-flash</p>
          </div>
          <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800">
            <span className="text-slate-400">Default Top-K Retrieval</span>
            <p className="text-sm font-semibold text-white mt-1">4 Chunks</p>
          </div>
          <div className="rounded-2xl bg-slate-900/80 p-4 border border-slate-800">
            <span className="text-slate-400">Similarity Cutoff</span>
            <p className="text-sm font-semibold text-white mt-1">40% Cosine Similarity</p>
          </div>
        </div>
      </div>
    </div>
  );
};
