import React from 'react';

export const StatCard = ({ title, value, subtitle, icon: Icon, color = 'brand' }) => {
  const colorMap = {
    brand: 'from-brand-600/20 to-indigo-600/10 text-brand-400 border-brand-500/20',
    emerald: 'from-emerald-600/20 to-teal-600/10 text-emerald-400 border-emerald-500/20',
    amber: 'from-amber-600/20 to-yellow-600/10 text-amber-400 border-amber-500/20',
    purple: 'from-purple-600/20 to-fuchsia-600/10 text-purple-400 border-purple-500/20',
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm hover:border-slate-700 transition-all">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
          <p className="mt-2 text-2xl font-bold tracking-tight text-white">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
        </div>
        <div className={`rounded-2xl bg-gradient-to-br p-3.5 border ${colorMap[color] || colorMap.brand}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
};
