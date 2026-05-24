import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(email, password, name);
    } catch (err) {
      setError(err.response?.data?.msg || 'Registration failed');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[80vh]">
      <div className="glass-card p-8 rounded-xl w-full max-w-md">
        <h2 className="text-3xl font-bold mb-6 text-center text-indigo-400">Register</h2>
        {error && <div className="bg-red-500/20 text-red-300 p-3 rounded mb-4">{error}</div>}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input type="text" value={name} onChange={e=>setName(e.target.value)} placeholder="Name" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="Email" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Password" className="p-3 bg-slate-800 rounded border border-slate-600 focus:border-indigo-500 outline-none" required />
          <button type="submit" className="p-3 bg-indigo-600 hover:bg-indigo-700 rounded text-white font-semibold transition">Register</button>
        </form>
        <div className="mt-4 text-center text-sm text-slate-400">
          Already have an account? <Link to="/login" className="text-indigo-400 hover:underline">Login</Link>
        </div>
      </div>
    </div>
  );
}
