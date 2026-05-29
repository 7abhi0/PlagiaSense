import React, { useState, useEffect, useRef } from 'react';
import api from '../utils/api';

function MetricBar({ label, value = 0, color = '#7C6FED', delay = 0 }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(value), 100 + delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className="font-bold text-slate-200">{Math.round(value)}/100</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${width}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function VerdictBanner({ isAI, confidence }) {
  if (isAI === null) return null;
  const config = isAI
    ? { label: 'Likely AI-Written', sub: `${confidence}% confidence`, bg: 'bg-red-900/30 border-red-500/40', text: 'text-red-300', icon: '🤖' }
    : confidence > 70
    ? { label: 'Likely Human', sub: `${confidence}% confidence`, bg: 'bg-green-900/30 border-green-500/40', text: 'text-green-300', icon: '✍️' }
    : { label: 'Inconclusive', sub: `${confidence}% confidence`, bg: 'bg-amber-900/30 border-amber-500/40', text: 'text-amber-300', icon: '🤔' };

  return (
    <div className={`border rounded-2xl px-6 py-5 flex items-center gap-4 animate-[fadeIn_0.5s_ease-out] ${config.bg}`}>
      <span className="text-4xl">{config.icon}</span>
      <div>
        <p className={`text-2xl font-black ${config.text}`}>{config.label}</p>
        <p className="text-slate-400 text-sm mt-0.5">{config.sub}</p>
      </div>
    </div>
  );
}

function getHeatmapStyle(score) {
  const opacity = Math.min((score / 100) * 0.55, 0.55);
  return {
    backgroundColor: `rgba(239, 68, 68, ${opacity})`,
    borderBottom: score > 40 ? `2px solid rgba(239, 68, 68, ${opacity + 0.25})` : 'none',
    padding: '2px 3px',
    borderRadius: '4px',
    marginRight: '2px',
    display: 'inline',
    cursor: 'default'
  };
}

export default function AIDetect() {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  const handleScan = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await api.post('/api/scan/detect', { text });
      setResult(res.data);
    } catch (err) {
      const msg = err?.response?.data?.error || err?.message || 'AI classification failed.';
      window.dispatchEvent(new CustomEvent('plagiasense:toast', { detail: { type: 'error', message: msg } }));
    } finally {
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
      link.download = `ai_report_${scanId}.pdf`;
      link.click();
    } catch {
      window.dispatchEvent(new CustomEvent('plagiasense:toast', { detail: { type: 'error', message: 'PDF download failed.' } }));
    } finally {
      setPdfLoading(false);
    }
  };

  // Derive metrics from result
  const vocabRichness = result ? Math.round((result.stylometry?.vocabulary_richness || 0) * 100) : 0;
  const entropy = result ? Math.min(Math.round((result.perplexity?.word_entropy || 0) * 12), 100) : 0;
  const predictability = result ? Math.max(0, 100 - Math.round((result.perplexity?.burstiness || 0) * 5)) : 0;
  const stylometric = result ? Math.round(100 - (result.stylometry?.stopword_density || 0) * 100) : 0;

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-8 animate-[fadeIn_0.4s_ease-out]">
      <div>
        <h1 className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
          Advanced AI Classifier
        </h1>
        <p className="text-slate-400 mt-1 text-sm">Ensemble detection pipeline — vocabulary, entropy, stylometrics, and perplexity analysis.</p>
      </div>

      {/* Verdict Banner */}
      {result && (
        <VerdictBanner
          isAI={result.ai_generated}
          confidence={result.ai_confidence}
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input */}
        <div className="lg:col-span-2 space-y-5">
          <div className="glass-card p-5 rounded-2xl border border-slate-700 bg-slate-800/80">
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Paste your essay or text here to detect AI authorship patterns..."
              className="w-full h-64 sm:h-72 p-4 bg-slate-900/80 rounded-xl border border-slate-700 focus:border-indigo-500 outline-none resize-none text-slate-100 text-sm transition focus:ring-2 focus:ring-indigo-500/20 placeholder-slate-600"
              disabled={loading}
            />
            <div className="flex items-center justify-between mt-3">
              <div className="flex gap-4 text-xs text-slate-500">
                <span>{wordCount} words</span>
                <span>{charCount} chars</span>
                {wordCount < 50 && wordCount > 0 && (
                  <span className="text-amber-500">⚠ Add more text for better accuracy</span>
                )}
              </div>
              <button
                onClick={handleScan}
                disabled={loading || !text.trim()}
                className="px-8 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 rounded-xl text-white font-bold transition shadow-lg shadow-blue-500/20 disabled:opacity-40 active:scale-95 text-sm"
              >
                {loading ? '🔄 Analyzing...' : '🧠 Analyze Writing Style'}
              </button>
            </div>
          </div>

          {/* Heatmap */}
          {result?.ai_heatmap && (
            <div className="glass-card p-5 rounded-2xl border border-slate-700 bg-slate-800/80 space-y-4 animate-[fadeIn_0.5s_ease-out]">
              <div className="flex items-center justify-between">
                <h2 className="text-slate-200 font-bold">AI Likelihood Heatmap</h2>
                <div className="flex items-center gap-2 text-xs">
                  <span className="w-3 h-3 rounded-sm bg-red-500/20 inline-block border border-red-400/50" />
                  <span className="text-slate-500">Higher = more AI</span>
                </div>
              </div>
              <p className="text-xs text-slate-500">Red intensity shows AI probability per sentence. Click a sentence to see details.</p>
              <div className="p-4 bg-slate-900 rounded-xl border border-slate-800 leading-8 text-slate-300 text-sm max-h-72 overflow-y-auto">
                {result.ai_heatmap.map((item, idx) => (
                  <span key={idx} style={getHeatmapStyle(item.ai_likelihood)}
                    title={`AI probability: ${item.ai_likelihood}%`}>
                    {item.text}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Metric Bars */}
          {result && (
            <div className="glass-card p-5 rounded-2xl border border-slate-700 bg-slate-800/80 space-y-5 animate-[fadeIn_0.6s_ease-out]">
              <h2 className="text-slate-200 font-bold">Writing Analysis Breakdown</h2>
              <MetricBar label="Vocabulary Richness" value={vocabRichness} color="#22c55e" delay={0} />
              <MetricBar label="Entropy Score" value={entropy} color="#7C6FED" delay={100} />
              <MetricBar label="Predictability Index" value={predictability} color="#f59e0b" delay={200} />
              <MetricBar label="Stylometric Fingerprint" value={stylometric} color="#3b82f6" delay={300} />
            </div>
          )}
        </div>

        {/* Right Panel */}
        <div className="space-y-4">
          {result ? (
            <>
              <div className="glass-card p-5 rounded-2xl border border-slate-700 bg-slate-800/80 space-y-4 animate-[fadeIn_0.5s_ease-out]">
                <h2 className="text-slate-300 font-bold text-center">Detection Result</h2>
                <div className="text-center py-3">
                  <div className={`text-5xl font-black mb-2 ${result.ai_generated ? 'text-red-400' : 'text-green-400'}`}>
                    {result.ai_confidence}%
                  </div>
                  <div className={`text-sm font-semibold ${result.ai_generated ? 'text-red-400' : 'text-green-400'}`}>
                    {result.ai_generated ? 'AI Generated' : 'Human Written'}
                  </div>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-1000 ${result.ai_generated ? 'bg-red-500' : 'bg-green-500'}`}
                    style={{ width: `${result.ai_confidence}%` }} />
                </div>
                <button onClick={() => downloadPDF(result.scan_id)} disabled={pdfLoading}
                  className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-indigo-500/40 rounded-xl text-slate-200 font-bold transition text-sm active:scale-95 disabled:opacity-40">
                  {pdfLoading ? '⏳ Generating...' : '📥 Download PDF Report'}
                </button>
              </div>

              {/* Detailed Metrics */}
              <div className="glass-card p-5 rounded-2xl border border-slate-700 bg-slate-800/80 space-y-3 animate-[fadeIn_0.6s_ease-out]">
                <h3 className="text-indigo-400 font-bold text-sm uppercase tracking-wider">Stylometric Details</h3>
                {[
                  { label: 'Avg Sentence Length', value: `${result.stylometry?.avg_sentence_length} words` },
                  { label: 'Sentence Variance', value: result.stylometry?.sentence_length_variance },
                  { label: 'Stopword Density', value: `${Math.round((result.stylometry?.stopword_density || 0) * 100)}%` },
                  { label: 'Burstiness', value: result.perplexity?.burstiness },
                  { label: 'Duplicate Bigrams', value: `${Math.round((result.perplexity?.duplicate_bigram_ratio || 0) * 100)}%` },
                  { label: 'Word Entropy', value: result.perplexity?.word_entropy },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between items-center text-sm border-b border-slate-700/40 pb-2 last:border-0 last:pb-0">
                    <span className="text-slate-400">{label}</span>
                    <span className="font-semibold text-slate-200">{value}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="glass-card p-5 rounded-2xl border border-slate-700/40 bg-slate-800/30 text-center space-y-3">
              <div className="text-5xl">🧠</div>
              <h3 className="text-slate-300 font-bold">AI Detection Ready</h3>
              <p className="text-slate-500 text-sm">Paste text to analyze for AI authorship patterns.</p>
              <div className="pt-2 space-y-2 text-xs text-slate-600 text-left">
                <p>✓ Vocabulary richness analysis</p>
                <p>✓ Entropy & burstiness metrics</p>
                <p>✓ Stylometric fingerprinting</p>
                <p>✓ Sentence-level heatmap</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
