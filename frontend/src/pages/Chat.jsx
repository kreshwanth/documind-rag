import React, { useState, useEffect, useRef } from 'react';
import { conversationApi, ragApi, documentApi } from '../services/api';
import { CitationCard } from '../components/CitationCard';
import ReactMarkdown from 'react-markdown';
import { 
  Brain, 
  Send, 
  Plus, 
  Trash2, 
  MessageSquare, 
  Sparkles, 
  SlidersHorizontal, 
  FileText, 
  Info, 
  Check, 
  Loader2, 
  BookOpen,
  Filter
} from 'lucide-react';

export const Chat = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputQuestion, setInputQuestion] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  
  // Available documents for targeted filtering
  const [availableDocs, setAvailableDocs] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  
  // RAG Hyperparameters
  const [topK, setTopK] = useState(4);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.15);
  const [showSettings, setShowSettings] = useState(false);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, sending]);

  // Load conversations and available documents
  useEffect(() => {
    const init = async () => {
      try {
        const [convRes, docRes] = await Promise.all([
          conversationApi.list(),
          documentApi.list(),
        ]);
        setConversations(convRes.data);
        setAvailableDocs(docRes.data.filter((d) => (d.status || '').toLowerCase() === 'completed'));

        if (convRes.data.length > 0) {
          selectConversation(convRes.data[0].id);
        }
      } catch (err) {
        console.error('Failed to initialize chat:', err);
      }
    };
    init();
  }, []);

  const selectConversation = async (convId) => {
    setActiveConvId(convId);
    setLoadingHistory(true);
    try {
      const res = await conversationApi.get(convId);
      setMessages(res.data.messages || []);
    } catch (err) {
      console.error('Failed to load conversation history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleNewConversation = () => {
    setActiveConvId(null);
    setMessages([]);
    setInputQuestion('');
  };

  const handleDeleteConversation = async (e, convId) => {
    e.stopPropagation();
    try {
      await conversationApi.delete(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        setActiveConvId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputQuestion.trim() || sending) return;

    const questionText = inputQuestion.trim();
    setInputQuestion('');

    // Optimistically append user message
    const tempUserMsg = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content: questionText,
      created_at: new Date().toISOString(),
      citations: [],
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setSending(true);

    try {
      const payload = {
        question: questionText,
        conversation_id: activeConvId || undefined,
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        top_k: topK,
        similarity_threshold: similarityThreshold,
      };

      const res = await ragApi.query(payload);
      const data = res.data;

      // Update active conversation ID if newly created
      if (!activeConvId && data.conversation_id) {
        setActiveConvId(data.conversation_id);
        // Refresh conversation list
        const convListRes = await conversationApi.list();
        setConversations(convListRes.data);
      }

      // Append assistant message with citations
      const assistantMsg = {
        id: data.message_id,
        role: 'assistant',
        content: data.answer,
        created_at: new Date().toISOString(),
        citations: data.sources || data.citations || [],
        is_fallback: data.is_fallback,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error('Error querying RAG:', err);
      const errorMsg = {
        id: 'err-' + Date.now(),
        role: 'assistant',
        content: 'An error occurred while generating the answer. Please ensure document vectors are ready or try again.',
        created_at: new Date().toISOString(),
        citations: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  };

  const toggleDocSelection = (docId) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const selectSingleDoc = (docId) => {
    if (!docId) {
      setSelectedDocIds([]);
    } else {
      setSelectedDocIds([docId]);
    }
  };

  return (
    <div className="flex h-[calc(100vh-6.5rem)] max-w-7xl mx-auto rounded-3xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-2xl backdrop-blur-md">
      {/* Sidebar - Conversation Threads & Document Filters */}
      <div className="hidden md:flex w-80 flex-col border-r border-slate-800 bg-slate-950/60">
        <div className="p-4 border-b border-slate-800/80">
          <button
            onClick={handleNewConversation}
            className="w-full flex items-center justify-center space-x-2 rounded-xl bg-brand-600/20 border border-brand-500/30 px-4 py-2.5 text-xs font-semibold text-brand-300 hover:bg-brand-600/30 hover:border-brand-500/50 transition-all cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            <span>New Chat Session</span>
          </button>
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <p className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">
            Chat History
          </p>
          {conversations.length === 0 ? (
            <p className="px-2 py-4 text-xs text-slate-500 text-center">No previous sessions</p>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                className={`group flex items-center justify-between rounded-xl px-3 py-2.5 text-xs font-medium cursor-pointer transition-all ${
                  activeConvId === conv.id
                    ? 'bg-brand-600/20 text-white border border-brand-500/30'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center space-x-2.5 truncate">
                  <MessageSquare className="h-3.5 w-3.5 shrink-0 text-brand-400" />
                  <span className="truncate">{conv.title}</span>
                </div>
                <button
                  onClick={(e) => handleDeleteConversation(e, conv.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 rounded transition-all"
                  title="Delete chat"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* Document Filter Section */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/40">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Filter className="h-3 w-3 text-brand-400" />
              Document Isolation
            </span>
            {selectedDocIds.length > 0 && (
              <button
                onClick={() => setSelectedDocIds([])}
                className="text-[10px] text-brand-400 hover:underline"
              >
                Reset (All)
              </button>
            )}
          </div>
          <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
            {availableDocs.length === 0 ? (
              <p className="text-[11px] text-slate-500">No completed documents available.</p>
            ) : (
              availableDocs.map((doc) => {
                const isSelected = selectedDocIds.includes(doc.id);
                return (
                  <div
                    key={doc.id}
                    onClick={() => toggleDocSelection(doc.id)}
                    className={`flex items-center space-x-2 rounded-lg px-2.5 py-2 text-[11px] cursor-pointer transition-all ${
                      isSelected
                        ? 'bg-indigo-600/30 text-indigo-200 border border-indigo-500/50 shadow-sm'
                        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200 border border-transparent'
                    }`}
                  >
                    <div
                      className={`h-4 w-4 rounded border flex items-center justify-center shrink-0 ${
                        isSelected
                          ? 'border-indigo-500 bg-indigo-600 text-white'
                          : 'border-slate-600 bg-slate-800'
                      }`}
                    >
                      {isSelected && <Check className="h-3 w-3" />}
                    </div>
                    <span className="truncate font-medium" title={doc.original_filename}>
                      {doc.original_filename}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col bg-slate-900/40 min-w-0">
        {/* Chat Header */}
        <div className="flex h-14 items-center justify-between px-6 border-b border-slate-800 bg-slate-950/40">
          <div className="flex items-center space-x-3 truncate">
            <div className="h-8 w-8 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 shrink-0">
              <Sparkles className="h-4 w-4" />
            </div>
            <div className="min-w-0">
              <h2 className="text-sm font-bold text-white truncate">Grounded Q&A Assistant</h2>
              <p className="text-[11px] text-slate-400 truncate">
                {selectedDocIds.length > 0
                  ? `Isolated Search: ${
                      availableDocs
                        .filter((d) => selectedDocIds.includes(d.id))
                        .map((d) => d.original_filename)
                        .join(', ') || 'Selected Documents'
                    }`
                  : 'Searching across all uploaded documents'}
              </p>
            </div>
          </div>

          {/* Settings Toggle */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`flex items-center space-x-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all shrink-0 ${
              showSettings
                ? 'bg-brand-600 text-white'
                : 'text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-700'
            }`}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            <span>RAG Tuning</span>
          </button>
        </div>

        {/* Interactive Document Isolation Bar */}
        <div className="px-6 py-2.5 bg-slate-950/80 border-b border-slate-800/70 flex items-center space-x-2 overflow-x-auto text-xs scrollbar-none">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1 shrink-0 mr-1">
            <FileText className="h-3 w-3 text-brand-400" />
            Target:
          </span>
          <button
            onClick={() => setSelectedDocIds([])}
            className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all shrink-0 cursor-pointer ${
              selectedDocIds.length === 0
                ? 'bg-brand-600 text-white shadow-glow'
                : 'bg-slate-800/80 text-slate-400 hover:bg-slate-700 hover:text-white border border-slate-700'
            }`}
          >
            All Documents
          </button>
          {availableDocs.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            return (
              <button
                key={doc.id}
                onClick={() => selectSingleDoc(isSelected && selectedDocIds.length === 1 ? null : doc.id)}
                className={`px-3 py-1 rounded-full text-[11px] font-medium transition-all flex items-center space-x-1.5 shrink-0 cursor-pointer ${
                  isSelected
                    ? 'bg-indigo-600 text-white shadow-glow border border-indigo-400/50'
                    : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700'
                }`}
                title={`Filter retrieval strictly to ${doc.original_filename}`}
              >
                <span>{doc.original_filename}</span>
                {isSelected && <Check className="h-3 w-3 text-indigo-200" />}
              </button>
            );
          })}
        </div>

        {/* Hyperparameters Config Bar */}
        {showSettings && (
          <div className="p-4 bg-slate-950/90 border-b border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <div className="flex justify-between font-medium text-slate-300 mb-1">
                <span>Top-K Chunks: {topK}</span>
                <span className="text-slate-500">Max chunks sent to LLM</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-brand-500 cursor-pointer"
              />
            </div>
            <div>
              <div className="flex justify-between font-medium text-slate-300 mb-1">
                <span>Cosine Similarity Threshold: {(similarityThreshold * 100).toFixed(0)}%</span>
                <span className="text-slate-500">Anti-hallucination cutoff</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="0.80"
                step="0.05"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(Number(e.target.value))}
                className="w-full accent-brand-500 cursor-pointer"
              />
            </div>
          </div>
        )}

        {/* Messages Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {loadingHistory ? (
            <div className="h-full flex items-center justify-center text-slate-400">
              <Loader2 className="h-6 w-6 animate-spin text-brand-400 mr-2" />
              <span className="text-xs">Loading messages...</span>
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 max-w-xl mx-auto">
              <div className="h-16 w-16 rounded-3xl bg-gradient-to-tr from-brand-600/30 to-indigo-500/20 border border-brand-500/30 flex items-center justify-center text-brand-400 mb-4 shadow-glow">
                <Brain className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-bold text-white">Ask Grounded Questions</h3>
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">
                DocuMind searches vector embeddings in PostgreSQL, strictly isolates retrieval to your selected document, and synthesizes answers with source citations.
              </p>
              
              {/* Context-aware suggestions */}
              <div className="mt-6 flex flex-wrap gap-2 justify-center">
                <button
                  onClick={() => {
                    const leaveDoc = availableDocs.find((d) => d.original_filename.toLowerCase().includes('leave'));
                    if (leaveDoc) setSelectedDocIds([leaveDoc.id]);
                    setInputQuestion('An employee has no remaining leave balance but needs additional time off. What options and approval process would apply in this situation?');
                  }}
                  className="rounded-xl bg-slate-800/80 px-3.5 py-2 text-xs text-slate-200 hover:bg-slate-700 hover:text-white border border-slate-700 transition-colors text-left"
                >
                  📄 <strong>Leave Policy:</strong> Zero balance & approval process
                </button>
                <button
                  onClick={() => {
                    const sugarDoc = availableDocs.find((d) => d.original_filename.toLowerCase().includes('sugar'));
                    if (sugarDoc) setSelectedDocIds([sugarDoc.id]);
                    setInputQuestion('What is the main objective of the WHO guideline on free sugars intake?');
                  }}
                  className="rounded-xl bg-slate-800/80 px-3.5 py-2 text-xs text-slate-200 hover:bg-slate-700 hover:text-white border border-slate-700 transition-colors text-left"
                >
                  🍬 <strong>WHO Sugar Guideline:</strong> Main guideline objective
                </button>
                <button
                  onClick={() => {
                    const leaveDoc = availableDocs.find((d) => d.original_filename.toLowerCase().includes('leave'));
                    if (leaveDoc) setSelectedDocIds([leaveDoc.id]);
                    setInputQuestion('An employee joins the company halfway through the year. How would their leave entitlement be handled?');
                  }}
                  className="rounded-xl bg-slate-800/80 px-3.5 py-2 text-xs text-slate-200 hover:bg-slate-700 hover:text-white border border-slate-700 transition-colors text-left"
                >
                  📅 <strong>Leave Policy:</strong> Joining halfway through year
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={msg.id || idx}
                className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-3xl rounded-3xl p-5 shadow-sm ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-r from-brand-600 to-indigo-600 text-white rounded-tr-sm'
                      : 'glass-panel rounded-tl-sm text-slate-200 border border-slate-800'
                  }`}
                >
                  {msg.role === 'assistant' && (
                    <div className="flex items-center space-x-2 mb-2 pb-2 border-b border-slate-800/60">
                      <Sparkles className="h-3.5 w-3.5 text-brand-400" />
                      <span className="text-[11px] font-bold text-brand-300 uppercase tracking-wider">
                        Grounded AI Response
                      </span>
                    </div>
                  )}

                  <div className="text-sm leading-relaxed whitespace-pre-wrap prose-dark">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>

                  {/* Citations List if available */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-2">
                      <div className="flex items-center space-x-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                        <BookOpen className="h-3.5 w-3.5 text-brand-400" />
                        <span>Source Citations ({msg.citations.length})</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                        {msg.citations.map((citation, citIdx) => (
                          <CitationCard key={citIdx} citation={citation} index={citIdx} />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {sending && (
            <div className="flex flex-col items-start">
              <div className="glass-panel max-w-lg rounded-3xl rounded-tl-sm p-4 border border-brand-500/20 shadow-glow flex items-center space-x-3 text-brand-300">
                <Loader2 className="h-4 w-4 animate-spin text-brand-400" />
                <span className="text-xs font-medium">
                  Retrieving vector chunks & generating grounded answer...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 bg-slate-950/70 border-t border-slate-800">
          <form onSubmit={handleSendMessage} className="relative flex items-center">
            <input
              type="text"
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              placeholder={
                selectedDocIds.length > 0
                  ? `Ask question about selected document(s)...`
                  : 'Ask a question grounded across all documents...'
              }
              disabled={sending}
              className="w-full rounded-2xl border border-slate-700 bg-slate-900/90 pl-5 pr-14 py-3.5 text-sm text-white placeholder-slate-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 transition-all shadow-inner"
            />
            <button
              type="submit"
              disabled={!inputQuestion.trim() || sending}
              className="absolute right-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 p-2.5 text-white shadow-glow hover:from-brand-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
          <div className="flex items-center justify-between text-[10px] text-slate-500 px-2 mt-2">
            <span>
              {selectedDocIds.length > 0
                ? '🔒 Document Isolation Active — Only chunks from selected document will be queried.'
                : 'Searching across all uploaded documents.'}
            </span>
            <span>Similarity cutoff: {(similarityThreshold * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
