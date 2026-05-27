import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import PlagiarismScan from './pages/PlagiarismScan';
import AIDetect from './pages/AIDetect';
import { ToastProvider } from './components/ToastProvider';

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <ToastProvider>
      <BrowserRouter>
        <div className="flex h-screen overflow-hidden bg-slate-900 text-slate-100">
          {isAuthenticated && <Sidebar />}
          <div className="flex-1 flex flex-col overflow-y-auto">
            {isAuthenticated && <Navbar />}
            <main className="p-6 flex-1">
              <Routes>
                <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
                <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/login" />} />
                <Route path="/" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
                <Route path="/scan" element={isAuthenticated ? <PlagiarismScan /> : <Navigate to="/login" />} />
                <Route path="/ai-detect" element={isAuthenticated ? <AIDetect /> : <Navigate to="/login" />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;

