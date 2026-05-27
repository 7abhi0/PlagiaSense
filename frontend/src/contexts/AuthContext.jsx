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

const getAuthErrorMessage = (error) => {
  if (error?.message === 'Network Error' || error?.code === 'ERR_NETWORK') {
    return 'Could not reach the backend API. Check VITE_API_URL or make sure the backend server is running.';
  }

  if (error?.code === 'auth/operation-not-allowed') {
    return 'Email/password sign-in is disabled in Firebase. Enable it in Firebase Console > Authentication > Sign-in method.';
  }

  if (error?.code === 'auth/user-not-found' || error?.code === 'auth/invalid-credential') {
    return 'Invalid email or password.';
  }

  if (error?.code === 'auth/email-already-in-use') {
    return 'An account already exists with this email.';
  }

  if (error?.code === 'auth/weak-password') {
    return 'Password should be at least 6 characters.';
  }

  return error.response?.data?.msg || error.message || 'Authentication failed';
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token);
      api.get('/api/auth/me').then(res => setUser(res.data)).catch(() => logout());
    } else {
      localStorage.removeItem('token');
      setUser(null);
    }
  }, [token]);

  const login = async (email, password) => {
    try {
      const credential = await signInWithEmailAndPassword(firebaseAuth, email, password);
      const idToken = await credential.user.getIdToken();
      const res = await api.post('/api/auth/firebase', { id_token: idToken });
      setToken(res.data.access_token);
      setUser({ email: res.data.email, name: res.data.name, role: res.data.role });
    } catch (error) {
      throw new Error(getAuthErrorMessage(error));
    }
  };

  const register = async (email, password, name) => {
    try {
      const credential = await createUserWithEmailAndPassword(firebaseAuth, email, password);
      if (name) {
        await updateProfile(credential.user, { displayName: name });
      }
      const idToken = await credential.user.getIdToken(true);
      const res = await api.post('/api/auth/firebase', { id_token: idToken, name });
      setToken(res.data.access_token);
      setUser({ email: res.data.email, name: res.data.name, role: res.data.role });
    } catch (error) {
      throw new Error(getAuthErrorMessage(error));
    }
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
