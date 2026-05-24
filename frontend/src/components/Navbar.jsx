import React from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function Navbar() {
  const { user, logout } = useAuth();
  return (
    <nav className="flex justify-between items-center p-4 border-b border-slate-700 bg-slate-800">
      <div className="text-xl font-bold text-indigo-400">PlagiaSense</div>
      <div className="flex gap-4 items-center">
        <span>{user?.name || user?.email}</span>
        <button onClick={logout} className="px-4 py-2 bg-red-600 rounded hover:bg-red-700 transition">Logout</button>
      </div>
    </nav>
  );
}
