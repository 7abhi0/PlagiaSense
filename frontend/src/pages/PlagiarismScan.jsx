import React, { useState } from 'react';
import api from '../utils/api';

export default function PlagiarismScan() {
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [activeTab, setActiveTab] = useState('highlighted'); // 'highlighted' or 'sources'
  const [pdfLoading, setPdfLoading] = useState(false);

  const handleScan = async () => {
    setLoading(true);
    setResult(null);
    setSelectedMatch(null);
    try {
      const formData = new FormData();
      if (file) {
        formData.append('file', file);
      } else {
        formData.append('text', text);
      }
      const res = await api.post('/scan/detect', formData);
      setResult(res.data);
    } catch (err) {
      alert('Plagiarism scan failed.');
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async (scanId) => {
    if (!scanId) return;
    setPdfLoading(true);
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
      alert('Failed to download PDF report.');
    } finally {
      setPdfLoading(false);
    }
  };

  const getCategoryClass = (category) => {
    switch (category) {
      case 'exact':
        return 'bg-red-500/20 hover:bg-red-500/30 border-b-2 border-red-500 cursor-pointer transition px-1 py-0.5 rounded';
      case 'paraphrased':
        return 'bg-orange-500/20 hover:bg-orange-500/30 border-b-2 border-orange-500 cursor-pointer transition px-1 py-0.5 rounded';
      case 'weak_paraphrased':
        return 'bg-yellow-500/20 hover:bg-yellow-500/30 border-b-2 border-yellow-400 cursor-pointer transition px-1 py-0.5 rounded';
      default:
        return 'text-slate-100';
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-[fadeIn_0.4s_ease-out]">
      <div>
        <h1 className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
          Semantic Plagiarism Scan
        </h1>
        <p className="text-slate-400 mt-1">Scan text against the web to detect direct copy-paste and semantic paraphrasing.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Input Panel */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 rounded-2xl border border-slate-700 bg-slate-800/80">
            <textarea 
              value={text} 
              onChange={e => {
                setText(e.target.value);
                if (file) setFile(null); // Clear file if user types
              }} 
              placeholder="Paste your document or academic essay here to perform deep web analysis..." 
              className="w-full h-80 p-4 bg-slate-900 rounded-xl border border-slate-700 focus:border-indigo-500 outline-none resize-none mb-4 text-slate-100 transition focus:ring-2 focus:ring-indigo-500/20"
              disabled={loading}
            ></textarea>
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-4 w-full sm:w-auto">
                <input 
                  type="file" 
                  accept=".txt,.pdf,.docx"
                  onChange={e => {
                    setFile(e.target.files[0]);
                    if (e.target.files[0]) setText(''); // Clear text if user uploads file
                  }} 
                  className="text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 transition" 
                />
              </div>
              <button 
                onClick={handleScan} 
                disabled={loading || (!text.trim() && !file)} 
                className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 rounded-xl text-white font-bold transition shadow-lg shadow-indigo-500/20 disabled:opacity-50 active:scale-95"
              >
                {loading ? 'Analyzing Web...' : 'Start Search'}
              </button>
            </div>
          </div>

          {result && (
            <div className="glass-card p-6 rounded-2xl border border-slate-700 bg-slate-800/80 space-y-6 animate-[fadeIn_0.5s_ease-out]">
              <div className="flex border-b border-slate-700">
                <button 
                  onClick={() => setActiveTab('highlighted')} 
                  className={`pb-3 px-4 font-bold border-b-2 transition ${activeTab === 'highlighted' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                >
                  Interactive Highlighted Document
                </button>
                <button 
                  onClick={() => setActiveTab('sources')} 
                  className={`pb-3 px-4 font-bold border-b-2 transition ${activeTab === 'sources' ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                >
                  All Matching Sources ({result.matches?.length || 0})
                </button>
              </div>

              {activeTab === 'highlighted' ? (
                <div className="p-4 bg-slate-900 rounded-xl border border-slate-800 leading-relaxed text-slate-300 max-h-96 overflow-y-auto">
                  {result.highlighted_sentences?.map((item, idx) => {
                    const isPlagiarized = item.category !== 'unique';
                    return (
                      <span 
                        key={idx} 
                        onClick={() => isPlagiarized && setSelectedMatch(item)}
                        className={`${getCategoryClass(item.category)} mr-1`}
                        title={isPlagiarized ? `Match found: ${item.similarity}% similarity` : 'Unique sentence'}
                      >
                        {item.text}{' '}
                      </span>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                  {result.matches?.length === 0 ? (
                    <p className="text-slate-400 text-center py-6">No matching online content detected. Document is 100% original!</p>
                  ) : (
                    result.matches?.map((match, idx) => (
                      <div key={idx} className="p-4 bg-slate-900/50 rounded-xl border border-slate-800 hover:border-slate-700 transition space-y-2">
                        <div className="flex justify-between items-start gap-4">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${match.category === 'exact' ? 'bg-red-900/30 text-red-400 border border-red-500/20' : 'bg-orange-900/30 text-orange-400 border border-orange-500/20'}`}>
                            {match.category.toUpperCase()} MATCH
                          </span>
                          <span className="text-sm font-bold text-indigo-400">{match.similarity_score}% Match</span>
                        </div>
                        <p className="text-slate-300 text-sm">"{match.original_text}"</p>
                        <div className="flex items-center justify-between text-xs text-slate-500 mt-2">
                          <a href={match.source_url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline truncate max-w-xs sm:max-w-md">
                            Source: {match.source_url}
                          </a>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Info Panel */}
        <div className="space-y-6">
          {/* Quick Metrics */}
          {result && (
            <div className="glass-card p-6 rounded-2xl border border-slate-700 bg-slate-800/80 text-center space-y-4 animate-[fadeIn_0.5s_ease-out]">
              <h2 className="text-lg font-bold text-slate-300">Scan Summary</h2>
              
              <div className="relative inline-flex items-center justify-center p-4">
                <div className="text-5xl font-black text-red-500">
                  {result.plagiarism_score}%
                </div>
              </div>
              <p className="text-sm text-slate-400 px-4">
                {result.plagiarism_score > 30 
                  ? "Attention: Significant similarity matched with public web pages."
                  : "Excellent: Low similarity detected. Safe to submit."
                }
              </p>
              
              <div className="border-t border-slate-700 pt-4 flex justify-around text-sm">
                <div>
                  <span className="block text-slate-400">Total Matches</span>
                  <span className="font-bold text-slate-200">{result.matches?.length || 0}</span>
                </div>
                <div>
                  <span className="block text-slate-400">Status</span>
                  <span className={`font-bold ${result.plagiarism_score > 30 ? 'text-red-400' : 'text-green-400'}`}>
                    {result.plagiarism_score > 30 ? 'High Plagiarism' : 'Passed'}
                  </span>
                </div>
              </div>

              <div className="border-t border-slate-700 pt-4">
                <button
                  onClick={() => downloadPDF(result.scan_id)}
                  disabled={pdfLoading}
                  className="w-full py-2.5 bg-slate-900 hover:bg-slate-850 border border-slate-700 rounded-xl text-slate-200 font-bold transition text-sm active:scale-95 disabled:opacity-50"
                >
                  {pdfLoading ? 'Generating PDF...' : 'Download PDF Report'}
                </button>
              </div>
            </div>
          )}

          {/* Interactive Comparison Pane */}
          {selectedMatch && (
            <div className="glass-card p-6 rounded-2xl border border-slate-700 bg-indigo-950/20 border-indigo-500/30 space-y-4 animate-[fadeIn_0.3s_ease-out]">
              <div className="flex justify-between items-center">
                <h3 className="text-md font-bold text-indigo-300">Source Comparison</h3>
                <button onClick={() => setSelectedMatch(null)} className="text-slate-400 hover:text-slate-200 text-xs">Close</button>
              </div>
              
              <div className="space-y-3">
                <div>
                  <span className="text-xs uppercase text-indigo-400 font-bold tracking-wider">Your Text</span>
                  <div className="p-3 bg-slate-900 rounded-lg text-sm border border-slate-800 text-slate-300">
                    "{selectedMatch.text}"
                  </div>
                </div>
                <div>
                  <span className="text-xs uppercase text-rose-400 font-bold tracking-wider">Matching Web Content ({selectedMatch.similarity}%)</span>
                  <div className="p-3 bg-slate-900 rounded-lg text-sm border border-slate-800 text-slate-300 italic">
                    "{selectedMatch.matched_text || selectedMatch.text}"
                  </div>
                </div>
                <div className="text-xs">
                  <span className="text-slate-400 block mb-1">Source link:</span>
                  <a href={selectedMatch.source_url} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline break-all block">
                    {selectedMatch.source_url}
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
