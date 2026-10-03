import React, { useState, useRef } from 'react';
import { UploadCloud, File, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { documentApi } from '../services/api';

export const FileDropzone = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    setError(null);
    setSuccessMsg(null);

    // Basic extension check
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'doc', 'txt', 'md'].includes(ext)) {
      setError(`Unsupported file type: .${ext}. Only PDF, DOCX, and TXT are supported.`);
      return;
    }

    // Size check (50MB)
    if (file.size > 50 * 1024 * 1024) {
      setError('File size exceeds the 50MB limit.');
      return;
    }

    setUploading(true);
    setProgress(10);

    try {
      const response = await documentApi.upload(file, (progressEvent) => {
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 90) / progressEvent.total);
          setProgress(percentCompleted);
        }
      });

      setProgress(100);
      setSuccessMsg(`"${file.name}" uploaded successfully! Ingestion & embedding in progress.`);
      if (onUploadSuccess) {
        onUploadSuccess(response.data);
      }
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to upload document.';
      setError(detail);
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`group relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-brand-500 bg-brand-500/10 scale-[1.01]'
            : 'border-slate-700 bg-slate-900/40 hover:border-slate-500 hover:bg-slate-900/70'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileSelect}
          accept=".pdf,.docx,.doc,.txt,.md"
          className="hidden"
          disabled={uploading}
        />

        <div className="mb-4 rounded-2xl bg-brand-500/10 p-4 text-brand-400 group-hover:scale-110 group-hover:bg-brand-500/20 transition-all border border-brand-500/20">
          {uploading ? (
            <Loader2 className="h-8 w-8 animate-spin text-brand-400" />
          ) : (
            <UploadCloud className="h-8 w-8" />
          )}
        </div>

        <h4 className="text-base font-semibold text-slate-100">
          {uploading ? 'Uploading & Processing Document...' : 'Upload enterprise documents'}
        </h4>
        <p className="mt-1 text-xs text-slate-400 max-w-sm">
          Drag and drop your files here, or <span className="text-brand-400 underline font-medium">browse</span>.
        </p>

        <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
          <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-300 border border-slate-700">
            PDF (Page-Accurate)
          </span>
          <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-300 border border-slate-700">
            DOCX (Word)
          </span>
          <span className="rounded-md bg-slate-800 px-2 py-0.5 text-[11px] font-medium text-slate-300 border border-slate-700">
            TXT / Markdown
          </span>
          <span className="rounded-md bg-slate-800/80 px-2 py-0.5 text-[11px] font-medium text-slate-400 border border-slate-700/50">
            Max 50MB
          </span>
        </div>

        {uploading && (
          <div className="mt-5 w-full max-w-xs">
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Transferring...</span>
              <span>{progress}%</span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full bg-gradient-to-r from-brand-500 to-indigo-400 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3 flex items-center space-x-2 rounded-xl bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-300">
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="mt-3 flex items-center space-x-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-3 text-xs text-emerald-300">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{successMsg}</span>
        </div>
      )}
    </div>
  );
};
