import React, { useEffect, useState } from 'react';
import { dashboardApi, documentApi } from '../services/api';
import { StatCard } from '../components/StatCard';
import { FileDropzone } from '../components/FileDropzone';
import { 
  FileText, 
  Layers, 
  HardDrive, 
  BookOpen, 
  Sparkles, 
  ArrowUpRight, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  Loader2
} from 'lucide-react';

export const Dashboard = ({ onNavigate }) => {
  const [stats, setStats] = useState(null);
  const [recentDocs, setRecentDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statsRes, docsRes] = await Promise.all([
        dashboardApi.getStats(),
        documentApi.list(),
      ]);
      setStats(statsRes.data);
      setRecentDocs(docsRes.data.slice(0, 5));
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll every 8 seconds for real-time document processing updates
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-brand-900/60 via-slate-900 to-indigo-950/60 p-8 border border-brand-500/20 shadow-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center space-x-2 rounded-full bg-brand-500/20 px-3 py-1 text-xs font-semibold text-brand-300 border border-brand-500/30 mb-3">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Grounded Enterprise RAG Active</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Enterprise Knowledge Intelligence
            </h1>
            <p className="mt-2 text-sm text-slate-300 leading-relaxed">
              Upload PDF, DOCX, or TXT documents to automatically extract, chunk, embed, and semantically query your organization's data with exact page-level source citations.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('chat')}
              className="flex items-center space-x-2 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-glow hover:from-brand-500 hover:to-indigo-500 transition-all cursor-pointer"
            >
              <Sparkles className="h-4 w-4" />
              <span>Launch AI Chat</span>
              <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatCard
          title="Indexed Documents"
          value={stats?.total_documents ?? (loading ? '...' : 0)}
          subtitle={`${stats?.completed_documents ?? 0} ready for retrieval`}
          icon={FileText}
          color="brand"
        />
        <StatCard
          title="Vector Chunks (pgvector)"
          value={stats?.total_chunks ?? (loading ? '...' : 0)}
          subtitle="768-dim embeddings"
          icon={Layers}
          color="purple"
        />
        <StatCard
          title="Extracted Pages"
          value={stats?.total_pages ?? (loading ? '...' : 0)}
          subtitle="Preserved metadata"
          icon={BookOpen}
          color="emerald"
        />
        <StatCard
          title="Storage Ingested"
          value={formatBytes(stats?.total_storage_bytes)}
          subtitle="PDF, DOCX, TXT"
          icon={HardDrive}
          color="amber"
        />
      </div>

      {/* Upload Zone & Recent Ingestions Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Upload Box */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-white">Quick Upload</h3>
            <span className="text-xs text-slate-400">Automatic Vector Indexing</span>
          </div>
          <div className="glass-panel rounded-3xl p-6 shadow-sm">
            <FileDropzone onUploadSuccess={() => fetchData()} />
          </div>
        </div>

        {/* Recent Ingestions Table */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-white">Recent Ingestion Activity</h3>
            <button
              onClick={() => onNavigate('documents')}
              className="text-xs font-semibold text-brand-400 hover:text-brand-300 underline cursor-pointer"
            >
              View all documents →
            </button>
          </div>

          <div className="glass-panel rounded-3xl overflow-hidden shadow-sm">
            {loading ? (
              <div className="p-8 text-center text-slate-400">
                <Loader2 className="h-6 w-6 animate-spin mx-auto text-brand-400 mb-2" />
                <p className="text-xs">Loading ingestion stats...</p>
              </div>
            ) : recentDocs.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                <FileText className="h-8 w-8 mx-auto text-slate-600 mb-2" />
                <p className="text-sm font-medium text-slate-300">No documents uploaded yet</p>
                <p className="text-xs text-slate-500 mt-1">Upload a PDF or Word document to get started.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-800">
                {recentDocs.map((doc) => (
                  <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-slate-800/30 transition-colors">
                    <div className="flex items-center space-x-3 min-w-0">
                      <div className="h-10 w-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 shrink-0">
                        <FileText className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-200 truncate">{doc.original_filename}</p>
                        <div className="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
                          <span className="uppercase text-[10px] font-bold text-slate-500">{doc.file_type}</span>
                          <span>•</span>
                          <span>{formatBytes(doc.file_size)}</span>
                          <span>•</span>
                          <span>{doc.total_pages} pages</span>
                          <span>•</span>
                          <span>{doc.total_chunks} chunks</span>
                        </div>
                      </div>
                    </div>

                    <div className="shrink-0 ml-4">
                      {doc.status === 'COMPLETED' && (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Indexed</span>
                        </span>
                      )}
                      {doc.status === 'PROCESSING' && (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-brand-500/10 px-2.5 py-1 text-xs font-medium text-brand-400 border border-brand-500/20 animate-pulse">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span>Chunking</span>
                        </span>
                      )}
                      {doc.status === 'PENDING' && (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-400 border border-amber-500/20">
                          <Clock className="h-3 w-3" />
                          <span>Queued</span>
                        </span>
                      )}
                      {doc.status === 'FAILED' && (
                        <span className="inline-flex items-center space-x-1 rounded-full bg-rose-500/10 px-2.5 py-1 text-xs font-medium text-rose-400 border border-rose-500/20">
                          <AlertCircle className="h-3 w-3" />
                          <span>Failed</span>
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
