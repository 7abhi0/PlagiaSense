import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const api = useMemo(
    () => ({
      push: (type, message) => {
        const id = `${Date.now()}_${Math.random().toString(16).slice(2)}`;
        setToasts((prev) => [...prev, { id, type, message }]);
        window.setTimeout(() => {
          setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 3500);
      }
    }),
    []
  );

  useEffect(() => {
    const handler = (e) => {
      const { type = 'error', message = '' } = e?.detail || {};
      api.push(type, message);
    };
    window.addEventListener('plagiasense:toast', handler);
    return () => window.removeEventListener('plagiasense:toast', handler);
  }, [api]);

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div
        className="fixed top-4 right-4 z-[9999] space-y-3 w-[92vw] max-w-sm"
        aria-live="polite"
        aria-relevant="additions"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`rounded-xl border px-4 py-3 shadow-lg backdrop-blur bg-slate-900/90 border-white/10 text-sm ` +
              (t.type === 'success'
                ? 'text-emerald-200'
                : t.type === 'warning'
                  ? 'text-amber-200'
                  : 'text-rose-200')}
          >
            <div className="font-semibold mb-1">
              {t.type === 'success' ? 'Success' : t.type === 'warning' ? 'Warning' : 'Error'}
            </div>
            <div className="text-slate-200/90">{t.message}</div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

