import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  updateProfile,
} from 'firebase/auth';
import { firebaseAuth } from '../lib/firebase';
import api from '../utils/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      api.get('/auth/me').then(res => setUser(res.data)).catch(() => logout());
    } else {
      localStorage.removeItem('token');
      setUser(null);
    }
  }, [token]);

  const login = async (email, password) => {
    const credential = await signInWithEmailAndPassword(firebaseAuth, email, password);
    const idToken = await credential.user.getIdToken();
    const res = await api.post('/auth/firebase', { id_token: idToken });
    setToken(res.data.access_token);
    setUser({ email: res.data.email, name: res.data.name, role: res.data.role });
  };

  const register = async (email, password, name) => {
    const credential = await createUserWithEmailAndPassword(firebaseAuth, email, password);
    if (name) {
      await updateProfile(credential.user, { displayName: name });
    }
    const idToken = await credential.user.getIdToken(true);
    const res = await api.post('/auth/firebase', { id_token: idToken, name });
    setToken(res.data.access_token);
    setUser({ email: res.data.email, name: res.data.name, role: res.data.role });
  };

  const logout = () => {
    signOut(firebaseAuth).catch(() => {});
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
