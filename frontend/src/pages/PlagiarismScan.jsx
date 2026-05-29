import React, { useState, useRef } from 'react';
import api from '../utils/api';

const STEPS = ['Uploading', 'Extracting Text', 'Scanning Web', 'Generating Report'];

function CircleScore({ score = 0, size = 140 }) {
  const r = 54;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(score, 100) / 100) * circ;
  const color = score > 50 ? '#ef4444' : score > 20 ? '#f59e0b' : '#22c55e';
  return (
    <svg width={size} height={size} viewBox="0 0 120 120">
      <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
      <circle cx="60" cy="60" r={r} fill="none" stroke={color} strokeWidth="10"
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round" transform="rotate(-90 60 60)"
        style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.4,0,0.2,1)' }} />
      <text x="60" y="55" textAnchor="middle" fill="white" fontSize="22" fontWeight="900">{score}%</text>
      <text x="60" y="72" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="9">Plagiarism</text>
    </svg>
  );
}

function ProgressSteps({ currentStep, loading }) {
  if (!loading) return null;
  return (
    <div className="flex items-center justify-center gap-1 sm:gap-2 py-3 animate-[fadeIn_0.3s_ease-out]">
      {STEPS.map((step, i) => (
        <React.Fragment key={step}>
          <div className="flex flex-col items-center gap-1">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-500 ${
              i < currentStep ? 'bg-indigo-600 text-white' :
              i === currentStep ? 'bg-indigo-500 text-white animate-pulse ring-2 ring-indigo-400/40' :
              'bg-slate-700 text-slate-500'
            }`}>
              {i < currentStep ? '✓' : i + 1}
            </div>
            <span className={`text-xs hidden sm:block transition-colors ${i <= currentStep ? 'text-indigo-400' : 'text-slate-600'}`}>
              {step}
            </span>
          </div>
          {i < STEPS.length - 1 && (
            <div className={`flex-1 h-0.5 mb-4 rounded transition-all duration-700 ${i < currentStep ? 'bg-indigo-600' : 'bg-slate-700'}`} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

function getCategoryClass(category) {
  switch (category) {
    case 'exact': return 'bg-red-500/25 border-b-2 border-red-400 cursor-pointer hover:bg-red-500/35 transition px-1 py-0.5 rounded';
    case 'paraphrased': return 'bg-orange-500/25 border-b-2 border-orange-400 cursor-pointer hover:bg-orange-500/35 transition px-1 py-0.5 rounded';
    case 'weak_paraphrased': return 'bg-yellow-500/20 border-b-2 border-yellow-400 cursor-pointer hover:bg-yellow-500/30 transition px-1 py-0.5 rounded';
    default: return 'text-slate-200';
  }
}

export default function PlagiarismScan() {
  const [text, setText] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [result, setResult] = useState(null);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [activeTab, setActiveTab] = useState('highlighted');
  const [pdfLoading, setPdfLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef();

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  const stepTimer = (cb) => {
    let s = 0;
    setStep(0);
    const intervals = [800, 2000, 4000];
    intervals.forEach((delay, i) => setTimeout(() => setStep(i + 1), delay));
    return cb();
  };

  const handleScan = async () => {
    setLoading(true);
    setResult(null);
    setSelectedMatch(null);
    setStep(0);

    const tick = () => {
      setStep(s => Math.min(s + 1, 3));
    };
    const t1 = setTimeout(tick, 900);
    const t2 = setTimeout(tick, 2500);
    const t3 = setTimeout(tick, 5000);

    try {
      const formData = new FormData();
      if (file) formData.append('file', file);
      else formData.append('text', text);
      const res = await api.post('/api/scan/detect', formData);
      setStep(4);
      setResult(res.data);
    } catch (err) {
      const msg = err?.response?.data?.error || err?.message || 'Plagiarism scan failed.';
      window.dispatchEvent(new CustomEvent('plagiasense:toast', { detail: { type: 'error', message: msg } }));
    } finally {
      clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
      setLoading(false);
    }
  };

  const downloadPDF = async (scanId) => {
    if (!scanId) return;
    setPdfLoading(true);
    try {
      const response = await api.get(`/reports/${scanId}/pdf`, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `plagiarism_report_${scanId}.pdf`;
      link.click();
    } catch {
      window.dispatchEvent(new CustomEvent('plagiasense:toast', { detail: { type: 'error', message: 'PDF download failed.' } }));
    } finally {
      setPdfLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) { setFile(dropped); setText(''); }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-8 animate-[fadeIn_0.4s_ease-out]">
      <div>
        <h1 className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
          Semantic Plagiarism Scan
        </h1>
        <p className="text-slate-400 mt-1 text-sm">Scan text against the web to detect direct copy-paste and semantic paraphrasing.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Input Panel */}
        <div className="lg:col-span-2 space-y-4">
          <div className="glass-card p-5 rounded-2xl border border-slate-700 bg-slate-800/80">

            {/* Tabs: Text or File */}
            <div className="flex gap-1 p-1 bg-slate-900/60 rounded-xl mb-4 w-fit">
              <button onClick={() => { setFile(null); }} className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition ${!file ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}>
                Paste Text
              </button>
              <button onClick={() => fileInputRef.current?.click()} className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition ${file ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}>
                Upload File
              </button>
            </div>

            {/* Text Area */}
            {!file && (
              <div className="relative">
                <textarea
                  value={text}
                  onChange={e => setText(e.target.value)}
                  placeholder="Paste your document or academic essay here..."
                  className="w-full h-64 sm:h-72 p-4 bg-slate-900/80 rounded-xl border border-slate-700 focus:border-indigo-500 outline-none resize-none text-slate-100 text-sm transition focus:ring-2 focus:ring-indigo-500/20 placeholder-slate-600"
                  disabled={loading}
                />
                <div className="absolute bottom-3 right-3 flex gap-3 text-xs text-slate-600">
                  <span>{wordCount} words</span>
                  <span>{charCount} chars</span>
                </div>
              </div>
            )}

            {/* Drop Zone */}
            {!text.trim() && (
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => !file && fileInputRef.current?.click()}
                className={`${file ? 'hidden' : text ? 'hidden' : ''} mt-3 border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${dragOver ? 'border-indigo-400 bg-indigo-500/10' : 'border-slate-700 hover:border-slate-500 hover:bg-slate-800/40'}`}
              >
                <div className="text-3xl mb-2">📁</div>
                <p className="text-slate-400 text-sm">Drop a file here or click to upload</p>
                <p className="text-slate-600 text-xs mt-1">PDF, DOCX, PPTX, TXT supported</p>
              </div>
            )}

            <input
              type="file"
              ref={fileInputRef}
              accept=".txt,.pdf,.docx,.pptx,.ppt"
              onChange={e => { const f = e.target.files[0]; if (f) { setFile(f); setText(''); } }}
              className="hidden"
            />

            {/* File selected indicator */}
            {file && (
              <div className="mt-3 flex items-center gap-3 p-3 bg-indigo-950/40 border border-indigo-500/30 rounded-xl">
                <span className="text-2xl">📄</span>
                <div className="flex-1 min-w-0">
                  <p className="text-indigo-300 text-sm font-semibold truncate">{file.name}</p>
                  <p className="text-slate-500 text-xs">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
                <button onClick={() => setFile(null)} className="text-slate-500 hover:text-slate-300 text-lg leading-none">×</button>
              </div>
            )}

            {/* Progress Steps */}
            {loading && (
              <div className="mt-4">
                <ProgressSteps currentStep={step} loading={loading} />
              </div>
            )}

            <div className="mt-4 flex justify-end">
              <button
                onClick={handleScan}
                disabled={loading || (!text.trim() && !file)}
                className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-xl text-white font-bold transition shadow-lg shadow-indigo-500/20 disabled:opacity-40 active:scale-95 text-sm"
              >
                {loading ? 'Scanning...' : '🔍 Start Scan'}
              </button>
            </div>
          </div>

          {/* Results */}
          {result && (
            <div className="glass-card p-5 rounded-2xl border border-slate-700 bg-slate-800/80 space-y-5 animate-[fadeIn_0.5s_ease-out]">
              {result.truncated && (
                <div className="flex items-start gap-2 bg-yellow-900/30 border border-yellow-500/30 text-yellow-200 px-4 py-3 rounded-xl text-sm">
                  <span>⚠️</span>
                  <span>Document truncated to 50,000 characters. Split into sections for full accuracy.</span>
                </div>
              )}

              {/* Tabs */}
              <div className="flex gap-1 border-b border-slate-700">
                {['highlighted', 'sources'].map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)}
                    className={`pb-3 px-4 font-bold text-sm border-b-2 transition capitalize ${activeTab === tab ? 'border-indigo-500 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}>
                    {tab === 'highlighted' ? '🎨 Highlighted Document' : `🔗 Sources (${result.matches?.length || 0})`}
                  </button>
                ))}
              </div>

              {activeTab === 'highlighted' ? (
                <div>
                  {/* Legend */}
                  <div className="flex flex-wrap gap-3 mb-3 text-xs">
                    <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-red-500/40 border-b border-red-400 inline-block" />Exact match</span>
                    <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-orange-500/40 border-b border-orange-400 inline-block" />Paraphrased</span>
                    <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-yellow-500/30 border-b border-yellow-400 inline-block" />Weak match</span>
                    <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-slate-700 inline-block" />Original</span>
                  </div>
                  <div className="p-4 bg-slate-900 rounded-xl border border-slate-800 leading-8 text-slate-300 text-sm max-h-80 overflow-y-auto">
                    {result.highlighted_sentences?.map((item, idx) => (
                      <span key={idx}
                        onClick={() => item.category !== 'unique' && setSelectedMatch(item)}
                        className={`${getCategoryClass(item.category)} mr-0.5`}
                        title={item.category !== 'unique' ? `${item.similarity}% match` : 'Original'}>
                        {item.text}{' '}
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                  {result.matches?.length === 0 ? (
                    <div className="text-center py-8">
                      <div className="text-4xl mb-2">✅</div>
                      <p className="text-green-400 font-semibold">No matching sources found!</p>
                      <p className="text-slate-500 text-sm mt-1">Document appears to be original.</p>
                    </div>
                  ) : result.matches?.map((match, idx) => (
                    <div key={idx} className="p-4 bg-slate-900/60 rounded-xl border border-slate-800 hover:border-indigo-500/30 transition space-y-2">
                      <div className="flex flex-wrap items-center gap-2 justify-between">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${match.category === 'exact' ? 'bg-red-900/40 text-red-300 border border-red-500/30' : 'bg-orange-900/40 text-orange-300 border border-orange-500/30'}`}>
                          {(match.category || 'match').replace('_', ' ').toUpperCase()}
                        </span>
                        <span className="text-indigo-400 font-bold text-sm">{match.similarity_score}% match</span>
                      </div>
                      <p className="text-slate-300 text-sm italic">"{match.original_text?.substring(0, 150)}{match.original_text?.length > 150 ? '...' : ''}"</p>
                      <a href={match.source_url} target="_blank" rel="noopener noreferrer"
                        className="text-indigo-400 hover:text-indigo-300 hover:underline text-xs truncate block transition">
                        🔗 {match.source_url}
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Summary Panel */}
        <div className="space-y-4">
          {result ? (
            <>
              <div className="glass-card p-5 rounded-2xl border border-slate-700 bg-slate-800/80 text-center space-y-4 animate-[fadeIn_0.5s_ease-out]">
                <h2 className="text-slate-300 font-bold">Scan Summary</h2>
                <div className="flex justify-center py-2">
                  <CircleScore score={Number(result.plagiarism_score) || 0} />
                </div>
                <p className={`text-sm px-2 font-medium ${result.plagiarism_score > 30 ? 'text-red-400' : result.plagiarism_score > 10 ? 'text-amber-400' : 'text-green-400'}`}>
                  {result.plagiarism_score > 50 ? '🚨 High plagiarism detected' :
                   result.plagiarism_score > 20 ? '⚠️ Moderate similarity found' :
                   '✅ Low similarity — safe to submit'}
                </p>
                <div className="border-t border-slate-700 pt-4 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="block text-slate-500 text-xs mb-1">Matches</span>
                    <span className="font-bold text-slate-200 text-lg">{result.matches?.length || 0}</span>
                  </div>
                  <div>
                    <span className="block text-slate-500 text-xs mb-1">Status</span>
                    <span className={`font-bold ${result.plagiarism_score > 30 ? 'text-red-400' : 'text-green-400'}`}>
                      {result.plagiarism_score > 30 ? 'Review' : 'Passed'}
                    </span>
                  </div>
                  {result.chunks_scanned > 1 && (
                    <div className="col-span-2">
                      <span className="block text-slate-500 text-xs mb-1">Sections Scanned</span>
                      <span className="font-bold text-indigo-400">{result.chunks_scanned}</span>
                    </div>
                  )}
                </div>
                <button onClick={() => downloadPDF(result.scan_id)} disabled={pdfLoading}
                  className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-indigo-500/40 rounded-xl text-slate-200 font-bold transition text-sm active:scale-95 disabled:opacity-40">
                  {pdfLoading ? '⏳ Generating...' : '📥 Download PDF Report'}
                </button>
              </div>

              {/* Word Stats */}
              {result.word_count && (
                <div className="glass-card p-4 rounded-2xl border border-slate-700 bg-slate-800/80 text-sm">
                  <h3 className="text-slate-400 font-semibold mb-3 text-xs uppercase tracking-wider">Document Stats</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Words</span>
                      <span className="font-bold text-slate-300">{result.word_count?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">AI Confidence</span>
                      <span className={`font-bold ${result.ai_confidence > 60 ? 'text-amber-400' : 'text-green-400'}`}>
                        {result.ai_confidence}%
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="glass-card p-5 rounded-2xl border border-slate-700/40 bg-slate-800/30 text-center space-y-3">
              <div className="text-5xl">🛡️</div>
              <h3 className="text-slate-300 font-bold">Ready to Scan</h3>
              <p className="text-slate-500 text-sm">Paste text or upload a document to check for plagiarism across the web.</p>
              <div className="pt-2 space-y-2 text-xs text-slate-600">
                <p>✓ Semantic similarity detection</p>
                <p>✓ PDF, DOCX, PPTX support</p>
                <p>✓ Long document chunking</p>
                <p>✓ Source URL identification</p>
              </div>
            </div>
          )}

          {/* Comparison pane */}
          {selectedMatch && (
            <div className="glass-card p-5 rounded-2xl border border-indigo-500/30 bg-indigo-950/20 space-y-4 animate-[fadeIn_0.3s_ease-out]">
              <div className="flex justify-between items-center">
                <h3 className="text-indigo-300 font-bold text-sm">Source Comparison</h3>
                <button onClick={() => setSelectedMatch(null)} className="text-slate-500 hover:text-slate-300 text-sm transition">✕</button>
              </div>
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-indigo-400 text-xs font-bold uppercase tracking-wider block mb-1">Your Text</span>
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-slate-300">"{selectedMatch.text}"</div>
                </div>
                <div>
                  <span className="text-rose-400 text-xs font-bold uppercase tracking-wider block mb-1">Web Match ({selectedMatch.similarity}%)</span>
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 text-slate-400 italic">"{selectedMatch.matched_text || selectedMatch.text}"</div>
                </div>
                <a href={selectedMatch.source_url} target="_blank" rel="noopener noreferrer"
                  className="text-indigo-400 hover:underline text-xs break-all block transition">
                  🔗 {selectedMatch.source_url}
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
