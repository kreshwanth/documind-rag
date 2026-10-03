import React, { useState, useEffect } from 'react';
import { searchApi, documentApi } from '../services/api';
import { Search as SearchIcon, BookOpen, Sparkles, Filter, Check, Loader2, FileText } from 'lucide-react';

export const Search = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [topK, setTopK] = useState(5);
  const [threshold, setThreshold] = useState(0.15);
  const [availableDocs, setAvailableDocs] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    const fetchDocs = async () => {
      try {
        const res = await documentApi.list();
        setAvailableDocs(res.data.filter((d) => (d.status || '').toLowerCase() === 'completed'));
      } catch (err) {
        console.error('Failed to load documents for search:', err);
      }
    };
    fetchDocs();
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setHasSearched(true);
    try {
      const res = await searchApi.search({
        query: query.trim(),
        top_k: topK,
        similarity_threshold: threshold,
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
      });
      setResults(res.data.results || []);
    } catch (err) {
      console.error('Vector search error:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleDoc = (id) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Semantic Vector Search</h1>
        <p className="text-xs text-slate-400 mt-1">
          Directly inspect cosine similarity vector search results in PostgreSQL pgvector without LLM answer synthesis.
        </p>
      </div>

      {/* Search & Filters */}
      <div className="glass-panel rounded-3xl p-6 space-y-4 shadow-sm">
        <form onSubmit={handleSearch} className="relative flex items-center">
          <SearchIcon className="pointer-events-none absolute left-4 h-5 w-5 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a natural-language query to find vector matches..."
            className="w-full rounded-2xl border border-slate-700 bg-slate-900/90 pl-12 pr-28 py-3.5 text-sm text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 transition-all shadow-inner"
          />
          <button
            type="submit"
            disabled={!query.trim() || loading}
            className="absolute right-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-glow hover:from-brand-500 hover:to-indigo-500 disabled:opacity-40 transition-all cursor-pointer"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search Chunks'}
          </button>
        </form>

        {/* Hyperparameter Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2 text-xs">
          <div>
            <div className="flex justify-between font-medium text-slate-300 mb-1">
              <span>Top-K: {topK}</span>
            </div>
            <input
              type="range"
              min="1"
              max="15"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full accent-brand-500 cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between font-medium text-slate-300 mb-1">
              <span>Similarity Cutoff: {(threshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.80"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="w-full accent-brand-500 cursor-pointer"
            />
          </div>

          <div className="sm:col-span-2">
            <span className="block font-medium text-slate-300 mb-1 flex items-center gap-1.5">
              <Filter className="h-3 w-3 text-brand-400" />
              Document Filter ({selectedDocIds.length > 0 ? selectedDocIds.length : 'All'} active)
            </span>
            <div className="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto">
              {availableDocs.map((d) => (
                <button
                  type="button"
                  key={d.id}
                  onClick={() => toggleDoc(d.id)}
                  className={`rounded-lg px-2.5 py-1 text-[11px] font-medium border transition-all ${
                    selectedDocIds.includes(d.id)
                      ? 'bg-brand-600/30 border-brand-500 text-brand-200'
                      : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {d.original_filename}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-white">Retrieved Vector Chunks</h3>
          {hasSearched && (
            <span className="text-xs text-slate-400">Found {results.length} matching passages</span>
          )}
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 glass-panel rounded-3xl">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-brand-400 mb-3" />
            <p className="text-xs">Computing cosine similarities in pgvector...</p>
          </div>
        ) : !hasSearched ? (
          <div className="p-12 text-center text-slate-400 glass-panel rounded-3xl">
            <SearchIcon className="h-10 w-10 mx-auto text-slate-600 mb-3" />
            <p className="text-base font-semibold text-slate-300">Ready for semantic search</p>
            <p className="text-xs text-slate-500 mt-1">Enter a search phrase to inspect top-K retrieved chunk vectors.</p>
          </div>
        ) : results.length === 0 ? (
          <div className="p-12 text-center text-slate-400 glass-panel rounded-3xl">
            <FileText className="h-10 w-10 mx-auto text-slate-600 mb-3" />
            <p className="text-base font-semibold text-slate-300">No matching chunks found</p>
            <p className="text-xs text-slate-500 mt-1">Try lowering the similarity threshold or broadening your query.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {results.map((hit, idx) => (
              <div key={hit.chunk_id || idx} className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2.5">
                    <span className="rounded bg-brand-500/20 px-2 py-0.5 text-xs font-semibold text-brand-300 border border-brand-500/30">
                      Rank #{idx + 1}
                    </span>
                    <span className="text-xs font-bold text-white">
                      {hit.document_name}
                    </span>
                    {hit.page_number !== null && (
                      <span className="rounded bg-indigo-500/20 px-2 py-0.5 text-[11px] font-medium text-indigo-300 border border-indigo-500/30">
                        Page {hit.page_number}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center space-x-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>{(hit.similarity_score * 100).toFixed(1)}% Cosine Similarity</span>
                  </div>
                </div>

                <div className="rounded-xl bg-slate-950/70 p-4 border border-slate-800/80 text-xs leading-relaxed text-slate-200 font-mono whitespace-pre-wrap">
                  {hit.content}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
