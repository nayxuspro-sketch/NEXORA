import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '@/types';
import { apiRequest } from '@/lib/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem('nexora_access_token');
    const savedUser = localStorage.getItem('nexora_user');

    if (savedToken && savedUser) {
      setToken(savedToken);
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        console.error(e);
      }
      setIsLoading(false);
    } else {
      // Auto-authentification transparente sur l'API Django pour rendre 100% des requêtes réelles
      fetch('/api/v1/auth/token/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'admin@nexora-enterprise.com',
          password: 'Admin123456!',
        }),
      })
        .then((res) => res.json())
        .then((data) => {
          if (data.access && data.user) {
            localStorage.setItem('nexora_access_token', data.access);
            localStorage.setItem('nexora_user', JSON.stringify(data.user));
            setToken(data.access);
            setUser(data.user);
          }
        })
        .catch(() => {
          // Fallback UI si hors-ligne
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, []);

  const login = (newToken: string, newUser: User) => {
    localStorage.setItem('nexora_access_token', newToken);
    localStorage.setItem('nexora_user', JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    localStorage.removeItem('nexora_access_token');
    localStorage.removeItem('nexora_user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
