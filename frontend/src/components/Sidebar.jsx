import React from 'react';
import { Link } from 'react-router-dom';

export default function Sidebar() {
  return (
    <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col p-4 gap-4">
      <div className="text-2xl font-black text-indigo-500 mb-8">PS.</div>
      <Link to="/" className="p-2 hover:bg-slate-700 rounded transition">Dashboard</Link>
      <Link to="/scan" className="p-2 hover:bg-slate-700 rounded transition">Plagiarism Scan</Link>
      <Link to="/ai-detect" className="p-2 hover:bg-slate-700 rounded transition">AI Detection</Link>
    </div>
  );
}
