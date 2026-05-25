import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('demo@plagiasense.com');
  const [password, setPassword] = useState('Password123');
  const [error, setError] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
    } catch (err) {
      setError(err.response?.data?.msg || err.message || 'Login failed');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <div className="glass-card p-8 rounded-xl w-full max-w-md">
        <h2 className="text-3xl font-bold mb-6 text-center text-indigo-400">Login</h2>
        {error && <div className="bg-red-500/20 text-red-300 p-3 rounded mb-4">{error}</div>}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <button type="submit" className="p-3 bg-indigo-600 hover:bg-indigo-700 rounded text-white font-semibold transition">Login</button>
        </form>
        <div className="mt-4 text-center text-sm text-slate-400">
          Don't have an account? <Link to="/register" className="text-indigo-400 hover:underline">Register</Link>
        </div>
      </div>
    </div>
  );
}
