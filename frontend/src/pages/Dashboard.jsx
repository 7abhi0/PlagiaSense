import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../utils/api';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ total_scans: 0, avg_plagiarism: 0, avg_ai_confidence: 0 });
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pdfLoading, setPdfLoading] = useState({});

  const fetchDashboardData = async () => {
    try {
      const [statsRes, scansRes] = await Promise.all([
        api.get('/reports/stats'),
        api.get('/reports')
      ]);
      setStats(statsRes.data);
      setScans(scansRes.data);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const downloadPDF = async (scanId) => {
    setPdfLoading(prev => ({ ...prev, [scanId]: true }));
    try {
      const response = await api.get(`/reports/${scanId}/pdf`, {
        responseType: 'blob'
      });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `report_${scanId}.pdf`;
      link.click();
    } catch (err) {
      window.dispatchEvent(new CustomEvent('plagiasense:toast', { detail: { type: 'error', message: 'Failed to download PDF report.' } }));
    } finally {
      setPdfLoading(prev => ({ ...prev, [scanId]: false }));
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-[fadeIn_0.5s_ease-out]">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
            Welcome back, {user?.name || 'User'}
          </h1>
          <p className="text-slate-400 mt-1">Here is a summary of your recent document scan telemetry and analysis history.</p>
        </div>
        <div className="flex gap-3">
          <Link to="/scan" className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-750 hover:to-purple-750 text-white rounded-xl font-bold transition text-sm text-center shadow-lg shadow-indigo-500/20 active:scale-95">
            Scan Plagiarism
          </Link>
          <Link to="/ai-detect" className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl font-bold transition text-sm text-center active:scale-95">
            AI Classifier
          </Link>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md hover:border-indigo-500/40 hover:shadow-indigo-500/5 transition-all duration-300 transform hover:-translate-y-1">
          <h3 className="text-slate-400 font-medium text-sm uppercase tracking-wider mb-2">Total Documents Scanned</h3>
          <p className="text-5xl font-black text-indigo-400">{loading ? '...' : stats.total_scans}</p>
        </div>
        <div className="glass-card p-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md hover:border-red-500/40 hover:shadow-red-500/5 transition-all duration-300 transform hover:-translate-y-1">
          <h3 className="text-slate-400 font-medium text-sm uppercase tracking-wider mb-2">Average Plagiarism Score</h3>
          <p className="text-5xl font-black text-red-400">{loading ? '...' : `${stats.avg_plagiarism}%`}</p>
        </div>
        <div className="glass-card p-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md hover:border-blue-500/40 hover:shadow-blue-500/5 transition-all duration-300 transform hover:-translate-y-1">
          <h3 className="text-slate-400 font-medium text-sm uppercase tracking-wider mb-2">Average AI Probability</h3>
          <p className="text-5xl font-black text-blue-400">{loading ? '...' : `${stats.avg_ai_confidence}%`}</p>
        </div>
      </div>

      {/* Recent Scans Section */}
      <div className="glass-card p-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md">
        <h2 className="text-xl font-bold text-slate-200 mb-6">Recent Analysis Reports</h2>
        {loading ? (
          <div className="text-center py-12 text-slate-400 animate-pulse">Loading reports...</div>
        ) : scans.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-slate-700 rounded-xl">
            <p className="text-slate-400 mb-4">You haven't scanned any documents yet.</p>
            <Link to="/scan" className="text-indigo-400 hover:underline font-semibold">Start your first scan now &rarr;</Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-700/50 text-slate-400 text-sm uppercase tracking-wider">
                  <th className="pb-3 font-semibold">Excerpt</th>
                  <th className="pb-3 font-semibold">Plagiarism</th>
                  <th className="pb-3 font-semibold">AI Generated</th>
                  <th className="pb-3 font-semibold">Date</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-sm">
                {scans.map((scan) => (
                  <tr key={scan._id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="py-4 pr-4 max-w-xs sm:max-w-md truncate text-slate-200">
                      {scan.text_excerpt}
                    </td>
                    <td className="py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${scan.plagiarism_score > 30 ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'}`}>
                        {scan.plagiarism_score}%
                      </span>
                    </td>
                    <td className="py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${scan.ai_generated ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'}`}>
                        {scan.ai_generated ? `Yes (${Math.round(scan.ai_confidence)}%)` : `No (${Math.round(100 - scan.ai_confidence)}%)`}
                      </span>
                    </td>
                    <td className="py-4 text-slate-400">
                      {new Date(scan.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric'
                      })}
                    </td>
                    <td className="py-4 text-right">
                      <button 
                        onClick={() => downloadPDF(scan._id)} 
                        disabled={pdfLoading[scan._id]}
                        className="text-indigo-400 hover:text-indigo-300 font-bold transition disabled:opacity-50"
                      >
                        {pdfLoading[scan._id] ? 'Downloading...' : 'Download PDF'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
