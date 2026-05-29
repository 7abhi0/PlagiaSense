import React, { useEffect, useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import api from '../utils/api';
import { Link } from 'react-router-dom';

// Animated count-up hook
function useCountUp(target, duration = 1200, start = false) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!start || target === 0) { setValue(target); return; }
    let startTime = null;
    const step = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, start, duration]);
  return value;
}

// Mini donut chart SVG
function DonutChart({ plagPercent = 0, size = 120 }) {
  const r = 46;
  const circ = 2 * Math.PI * r;
  const plagOffset = circ - (plagPercent / 100) * circ;
  return (
    <svg width={size} height={size} viewBox="0 0 100 100">
      <circle cx="50" cy="50" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
      <circle cx="50" cy="50" r={r} fill="none" stroke="#ef4444" strokeWidth="10"
        strokeDasharray={circ} strokeDashoffset={plagOffset}
        strokeLinecap="round" transform="rotate(-90 50 50)"
        style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)' }} />
      <circle cx="50" cy="50" r={r} fill="none" stroke="#22c55e" strokeWidth="10"
        strokeDasharray={circ} strokeDashoffset={circ - (((100 - plagPercent) / 100) * circ)}
        strokeLinecap="round" transform={`rotate(${-90 + (plagPercent / 100) * 360} 50 50)`}
        style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)' }} />
      <text x="50" y="54" textAnchor="middle" fill="white" fontSize="16" fontWeight="bold">
        {plagPercent}%
      </text>
    </svg>
  );
}

// Mini sparkline SVG
function Sparkline({ data = [], color = '#7C6FED', height = 40 }) {
  if (data.length < 2) return <div className="h-10 flex items-center justify-center text-xs text-slate-500">No data yet</div>;
  const max = Math.max(...data, 1);
  const w = 200, h = height;
  const points = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - (v / max) * (h - 4) - 2}`).join(' ');
  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {data.map((v, i) => (
        <circle key={i} cx={(i / (data.length - 1)) * w} cy={h - (v / max) * (h - 4) - 2} r="3" fill={color} />
      ))}
    </svg>
  );
}

function getBadge(scan) {
  if (scan.ai_generated && scan.plagiarism_score > 20)
    return { label: 'AI + Plagiarism', cls: 'bg-purple-500/15 text-purple-300 border-purple-500/30' };
  if (scan.plagiarism_score > 30)
    return { label: 'Plagiarised', cls: 'bg-red-500/15 text-red-300 border-red-500/30' };
  if (scan.ai_generated)
    return { label: 'AI-Written', cls: 'bg-amber-500/15 text-amber-300 border-amber-500/30' };
  return { label: 'Clean', cls: 'bg-green-500/15 text-green-300 border-green-500/30' };
}

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ total_scans: 0, avg_plagiarism: 0, avg_ai_confidence: 0 });
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pdfLoading, setPdfLoading] = useState({});
  const [animStart, setAnimStart] = useState(false);

  const totalCount = useCountUp(stats.total_scans, 1000, animStart);
  const plagCount = useCountUp(Number(stats.avg_plagiarism) || 0, 1200, animStart);
  const aiCount = useCountUp(Number(stats.avg_ai_confidence) || 0, 1400, animStart);

  useEffect(() => {
    const fetchData = async () => {
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
        setTimeout(() => setAnimStart(true), 100);
      }
    };
    fetchData();
  }, []);

  const downloadPDF = async (scanId) => {
    setPdfLoading(prev => ({ ...prev, [scanId]: true }));
    try {
      const response = await api.get(`/reports/${scanId}/pdf`, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `report_${scanId}.pdf`;
      link.click();
    } catch {
      window.dispatchEvent(new CustomEvent('plagiasense:toast', { detail: { type: 'error', message: 'Failed to download PDF.' } }));
    } finally {
      setPdfLoading(prev => ({ ...prev, [scanId]: false }));
    }
  };

  // Build sparkline data from scans (last 7)
  const sparkData = scans.slice(0, 7).reverse().map(s => Number(s.plagiarism_score) || 0);
  const avgPlag = Number(stats.avg_plagiarism) || 0;

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-8 animate-[fadeIn_0.5s_ease-out]">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-2">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
            Welcome back, {user?.name || user?.email?.split('@')[0] || 'User'} 👋
          </h1>
          <p className="text-slate-400 mt-1 text-sm">Your document analysis overview and scan history.</p>
        </div>
        <div className="flex gap-3 flex-shrink-0">
          <Link to="/scan" className="px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl font-bold transition text-sm shadow-lg shadow-indigo-500/20 active:scale-95 whitespace-nowrap">
            + New Scan
          </Link>
          <Link to="/ai-detect" className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 hover:border-slate-600 rounded-xl font-bold transition text-sm active:scale-95 whitespace-nowrap">
            AI Classifier
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6">
        {/* Total Scans */}
        <div className="group relative overflow-hidden glass-card p-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md hover:border-indigo-500/50 hover:shadow-lg hover:shadow-indigo-500/10 transition-all duration-300 hover:-translate-y-1 cursor-default">
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <div className="flex items-start justify-between">
            <div>
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-3">Total Scanned</p>
              <p className="text-5xl font-black text-indigo-400 tabular-nums">
                {loading ? <span className="animate-pulse opacity-40">—</span> : totalCount}
              </p>
              <p className="text-slate-500 text-xs mt-2">documents analyzed</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-xl">📄</div>
          </div>
        </div>

        {/* Avg Plagiarism */}
        <div className="group relative overflow-hidden glass-card p-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md hover:border-red-500/50 hover:shadow-lg hover:shadow-red-500/10 transition-all duration-300 hover:-translate-y-1 cursor-default">
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <div className="flex items-start justify-between">
            <div>
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-3">Avg Plagiarism</p>
              <p className="text-5xl font-black text-red-400 tabular-nums">
                {loading ? <span className="animate-pulse opacity-40">—</span> : `${plagCount}%`}
              </p>
              <p className="text-slate-500 text-xs mt-2">across all documents</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center text-xl">🔍</div>
          </div>
        </div>

        {/* Avg AI Probability */}
        <div className="group relative overflow-hidden glass-card p-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-300 hover:-translate-y-1 cursor-default">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          <div className="flex items-start justify-between">
            <div>
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-3">Avg AI Probability</p>
              <p className="text-5xl font-black text-blue-400 tabular-nums">
                {loading ? <span className="animate-pulse opacity-40">—</span> : `${aiCount}%`}
              </p>
              <p className="text-slate-500 text-xs mt-2">AI-generated likelihood</p>
            </div>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-xl">🤖</div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      {!loading && scans.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
          {/* Donut Chart */}
          <div className="glass-card p-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md">
            <h3 className="text-slate-300 font-bold text-sm mb-4">Plagiarism vs Original Ratio</h3>
            <div className="flex items-center justify-around">
              <DonutChart plagPercent={Math.round(avgPlag)} />
              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span className="text-slate-400">Plagiarised</span>
                  <span className="ml-auto font-bold text-red-400">{Math.round(avgPlag)}%</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500" />
                  <span className="text-slate-400">Original</span>
                  <span className="ml-auto font-bold text-green-400">{Math.round(100 - avgPlag)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sparkline */}
          <div className="glass-card p-6 rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md">
            <h3 className="text-slate-300 font-bold text-sm mb-4">Recent Plagiarism Scores</h3>
            <div className="mt-2">
              <Sparkline data={sparkData} color="#7C6FED" height={60} />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mt-2">
              <span>Oldest</span>
              <span>Latest</span>
            </div>
          </div>
        </div>
      )}

      {/* Recent Scans Table */}
      <div className="glass-card rounded-2xl border border-slate-700/60 bg-slate-800/40 backdrop-blur-md overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-700/50 flex items-center justify-between">
          <h2 className="text-slate-200 font-bold text-lg">Recent Analysis Reports</h2>
          {scans.length > 0 && (
            <span className="text-xs text-slate-500 bg-slate-700/50 px-2.5 py-1 rounded-full">{scans.length} report{scans.length !== 1 ? 's' : ''}</span>
          )}
        </div>

        {loading ? (
          <div className="p-6 space-y-4">
            {[1,2,3].map(i => (
              <div key={i} className="h-12 bg-slate-700/30 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : scans.length === 0 ? (
          <div className="text-center py-16 px-6">
            <div className="text-6xl mb-4">📭</div>
            <p className="text-slate-400 text-lg font-medium mb-2">No scans yet</p>
            <p className="text-slate-500 text-sm mb-6">Run your first plagiarism check to see results here.</p>
            <Link to="/scan" className="inline-block px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl font-bold transition text-sm shadow-lg shadow-indigo-500/20 active:scale-95">
              Start your first scan →
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="border-b border-slate-700/50">
                <tr className="text-slate-400 text-xs uppercase tracking-widest">
                  <th className="px-6 py-3 font-semibold">Excerpt</th>
                  <th className="px-4 py-3 font-semibold">Status</th>
                  <th className="px-4 py-3 font-semibold">Plagiarism</th>
                  <th className="px-4 py-3 font-semibold">AI Prob</th>
                  <th className="px-4 py-3 font-semibold">Date</th>
                  <th className="px-4 py-3 font-semibold text-right">Report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {scans.map((scan, idx) => {
                  const badge = getBadge(scan);
                  return (
                    <tr key={scan._id || idx} className="hover:bg-slate-700/20 transition-colors group">
                      <td className="px-6 py-4 max-w-[200px] sm:max-w-xs truncate text-slate-300 text-sm">
                        {scan.text_excerpt}
                      </td>
                      <td className="px-4 py-4">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${badge.cls}`}>
                          {badge.label}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden hidden sm:block">
                            <div className="h-full bg-red-500 rounded-full transition-all duration-700"
                              style={{ width: `${Math.min(scan.plagiarism_score, 100)}%` }} />
                          </div>
                          <span className={`text-sm font-bold ${scan.plagiarism_score > 30 ? 'text-red-400' : 'text-green-400'}`}>
                            {scan.plagiarism_score}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <span className={`text-sm font-bold ${scan.ai_confidence > 60 ? 'text-amber-400' : 'text-slate-400'}`}>
                          {Math.round(scan.ai_confidence)}%
                        </span>
                      </td>
                      <td className="px-4 py-4 text-slate-400 text-sm whitespace-nowrap">
                        {new Date(scan.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="px-4 py-4 text-right">
                        <button onClick={() => downloadPDF(scan._id)} disabled={pdfLoading[scan._id]}
                          className="text-indigo-400 hover:text-indigo-300 font-semibold text-sm transition disabled:opacity-40 opacity-0 group-hover:opacity-100">
                          {pdfLoading[scan._id] ? '...' : '↓ PDF'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
