import React from 'react';
import { useAuth } from '../context/AuthContext';
import { LogOut, User as UserIcon, Brain, Sparkles, Search, Sliders, FileText, LayoutDashboard } from 'lucide-react';

export const Navbar = ({ currentTab, setCurrentTab }) => {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'documents', label: 'Documents', icon: FileText },
    { id: 'chat', label: 'AI Chat', icon: Sparkles },
    { id: 'search', label: 'Vector Search', icon: Search },
    { id: 'settings', label: 'Settings', icon: Sliders },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-900/80 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setCurrentTab('dashboard')}>
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-400 shadow-glow">
            <Brain className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xl font-bold tracking-tight text-white">DocuMind</span>
              <span className="rounded bg-brand-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-brand-300 border border-brand-500/30">
                RAG ENTERPRISE
              </span>
            </div>
            <p className="text-[11px] text-slate-400">PostgreSQL pgvector + Google Gemini</p>
          </div>
        </div>

        {/* Navigation tabs */}
        <nav className="hidden md:flex items-center space-x-1 rounded-xl bg-slate-800/60 p-1 border border-slate-700/50">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-medium rounded-lg transition-all ${
                  isActive
                    ? 'bg-brand-600 text-white shadow-sm'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* User profile & Logout */}
        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-3 pr-2 border-r border-slate-800">
            <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-brand-400">
              <UserIcon className="h-4 w-4" />
            </div>
            <div className="text-left">
              <p className="text-xs font-semibold text-slate-200">{user?.name}</p>
              <p className="text-[11px] text-slate-400">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={logout}
            className="flex items-center space-x-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-colors"
            title="Log Out"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
};
