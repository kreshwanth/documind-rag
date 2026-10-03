import React, { useEffect, useState } from 'react';
import { documentApi } from '../services/api';
import { FileDropzone } from '../components/FileDropzone';
import { 
  FileText, 
  Trash2, 
  Eye, 
  Search, 
  RefreshCw, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Loader2, 
  Layers, 
  Calendar,
  X,
  Plus
} from 'lucide-react';

export const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docDetails, setDocDetails] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const fetchDocs = async () => {
    try {
      const res = await documentApi.list();
      setDocuments(res.data);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
    const interval = setInterval(fetchDocs, 6000);
    return () => clearInterval(interval);
  }, []);

  const handleViewDetails = async (doc) => {
    setSelectedDoc(doc);
    setDetailsLoading(true);
    try {
      const res = await documentApi.get(doc.id);
      setDocDetails(res.data);
    } catch (err) {
      console.error('Failed to load document details:', err);
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete "${name}" and all its vector embeddings?`)) {
      return;
    }
    setDeletingId(id);
    try {
      await documentApi.delete(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      if (selectedDoc?.id === id) {
        setSelectedDoc(null);
      }
    } catch (err) {
      alert('Failed to delete document: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDeletingId(null);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const filteredDocs = documents.filter((d) =>
    d.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Enterprise Documents</h1>
          <p className="text-xs text-slate-400 mt-1">
            Manage your parsed knowledge base and inspect vector chunk distributions.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDocs}
            className="p-2.5 rounded-xl bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 transition-colors border border-slate-700"
            title="Refresh documents"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center space-x-2 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-glow hover:from-brand-500 hover:to-indigo-500 transition-all cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter documents by filename..."
          className="w-full rounded-2xl border border-slate-800 bg-slate-900/80 pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 transition-all"
        />
      </div>

      {/* Documents Table */}
      <div className="glass-panel rounded-3xl overflow-hidden shadow-sm">
        {loading && documents.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-brand-400 mb-3" />
            <p className="text-sm">Loading documents...</p>
          </div>
        ) : filteredDocs.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <FileText className="h-10 w-10 mx-auto text-slate-600 mb-3" />
            <p className="text-base font-semibold text-slate-300">No documents found</p>
            <p className="text-xs text-slate-500 mt-1">Upload a PDF, DOCX, or TXT file to start building your knowledge base.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-900/90 text-xs font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th scope="col" className="px-6 py-4">Document Name</th>
                  <th scope="col" className="px-6 py-4">Status</th>
                  <th scope="col" className="px-6 py-4">Size</th>
                  <th scope="col" className="px-6 py-4">Pages</th>
                  <th scope="col" className="px-6 py-4">Vector Chunks</th>
                  <th scope="col" className="px-6 py-4">Uploaded</th>
                  <th scope="col" className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-medium text-white flex items-center space-x-3">
                      <div className="h-8 w-8 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 shrink-0">
                        <FileText className="h-4 w-4" />
                      </div>
                      <span className="truncate max-w-xs" title={doc.original_filename}>
                        {doc.original_filename}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {((doc.status || '').toLowerCase() === 'completed') && (
                        <span className="inline-flex items-center space-x-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="h-3 w-3" />
                          <span>Indexed</span>
                        </span>
                      )}
                      {((doc.status || '').toLowerCase() === 'processing') && (
                        <span className="inline-flex items-center space-x-1.5 rounded-full bg-brand-500/10 px-2.5 py-1 text-xs font-medium text-brand-400 border border-brand-500/20 animate-pulse">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span>Chunking</span>
                        </span>
                      )}
                      {((doc.status || '').toLowerCase() === 'pending') && (
                        <span className="inline-flex items-center space-x-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-400 border border-amber-500/20">
                          <Clock className="h-3 w-3" />
                          <span>Queued</span>
                        </span>
                      )}
                      {((doc.status || '').toLowerCase() === 'failed') && (
                        <span className="inline-flex items-center space-x-1.5 rounded-full bg-rose-500/10 px-2.5 py-1 text-xs font-medium text-rose-400 border border-rose-500/20" title={doc.error_message}>
                          <AlertCircle className="h-3 w-3" />
                          <span>Failed</span>
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">{formatBytes(doc.file_size)}</td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-200">{doc.total_pages}</td>
                    <td className="px-6 py-4 text-xs font-medium text-slate-200">{doc.total_chunks}</td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        onClick={() => handleViewDetails(doc)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-brand-400 hover:bg-brand-500/10 transition-colors"
                        title="Inspect chunks & metadata"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.original_filename)}
                        disabled={deletingId === doc.id}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors disabled:opacity-50"
                        title="Delete document"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="relative w-full max-w-lg rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">Upload New Document</h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <FileDropzone
              onUploadSuccess={() => {
                fetchDocs();
                setTimeout(() => setShowUploadModal(false), 1200);
              }}
            />
          </div>
        </div>
      )}

      {/* Document Details & Chunk Viewer Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="relative w-full max-w-3xl max-h-[85vh] flex flex-col rounded-3xl border border-slate-700 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
                  <FileText className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white truncate max-w-md">
                    {selectedDoc.original_filename}
                  </h3>
                  <div className="flex items-center space-x-2 text-xs text-slate-400 mt-0.5">
                    <span>{selectedDoc.total_pages} Pages</span>
                    <span>•</span>
                    <span>{selectedDoc.total_chunks} Vector Chunks</span>
                    <span>•</span>
                    <span>{formatBytes(selectedDoc.file_size)}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => { setSelectedDoc(null); setDocDetails(null); }}
                className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="overflow-y-auto flex-1 py-4 space-y-4">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Vector Chunks & Page Attributions
              </h4>

              {detailsLoading ? (
                <div className="p-8 text-center text-slate-400">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto text-brand-400 mb-2" />
                  <p className="text-xs">Loading chunk vector representations...</p>
                </div>
              ) : docDetails?.chunks?.length === 0 ? (
                <p className="text-xs text-slate-500">No chunks indexed for this document.</p>
              ) : (
                <div className="space-y-3">
                  {docDetails?.chunks?.map((chunk, idx) => (
                    <div key={chunk.id} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="rounded bg-brand-500/20 px-2 py-0.5 text-[11px] font-semibold text-brand-300 border border-brand-500/30">
                          Chunk #{idx + 1}
                        </span>
                        <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[11px] font-medium text-indigo-300 border border-indigo-500/30">
                          Page {chunk.page_number}
                        </span>
                      </div>
                      <p className="text-xs leading-relaxed text-slate-300 font-mono whitespace-pre-wrap">
                        {chunk.content}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
