import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Sparkles, BookOpen } from 'lucide-react';

export const CitationCard = ({ citation, index }) => {
  const [expanded, setExpanded] = useState(false);
  const similarityPct = Math.round((citation.similarity_score || 0) * 100);

  return (
    <div className="group relative rounded-xl border border-slate-800 bg-slate-900/60 p-3 hover:border-brand-500/40 transition-all shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start space-x-2.5 min-w-0">
          <div className="mt-0.5 rounded-lg bg-brand-500/10 p-1.5 text-brand-400 border border-brand-500/20 shrink-0">
            <BookOpen className="h-3.5 w-3.5" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-200 truncate" title={citation.document_name}>
                {citation.document_name}
              </span>
              <span className="rounded bg-indigo-500/20 px-1.5 py-0.5 text-[10px] font-medium text-indigo-300 border border-indigo-500/30 shrink-0">
                Page {citation.page_number}
              </span>
            </div>
            {citation.chunk_index !== undefined && (
              <p className="text-[10px] text-slate-400 mt-0.5">
                Chunk #{citation.chunk_index + 1}
              </p>
            )}
          </div>
        </div>

        {/* Similarity Score Badge */}
        <div className="flex items-center space-x-1 shrink-0">
          <div className="text-right">
            <div className="flex items-center space-x-1 text-[11px] font-semibold text-emerald-400">
              <Sparkles className="h-3 w-3" />
              <span>{similarityPct}% match</span>
            </div>
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 text-slate-400 hover:text-slate-200 rounded transition-colors"
            title={expanded ? "Hide snippet" : "View source passage"}
          >
            {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {/* Snippet expandable block */}
      {expanded && (
        <div className="mt-2.5 rounded-lg bg-slate-950/70 p-2.5 border border-slate-800/80 text-[11px] leading-relaxed text-slate-300 font-mono">
          <p className="line-clamp-6 whitespace-pre-wrap">{citation.snippet}</p>
        </div>
      )}
    </div>
  );
};
