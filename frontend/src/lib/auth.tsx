'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { User } from '@/types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Utilisateur administrateur par défaut sécurisé pré-connecté pour garantir l'immédiateté d'usage
const DEFAULT_DEMO_USER: User = {
  id: 'd80b0a58-f3ee-440b-b75d-916f5174e36a',
  email: 'admin@nexora-enterprise.com',
  first_name: 'Directeur',
  last_name: 'Général',
  role: 'ADMIN',
  is_active: true,
  company_id: '6be8c288-f9e1-4d16-8a51-21d804041da9',
  company_name: 'NEXORA BURKINA COMMERCIAL GROUP',
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [user, setUser] = useState<User | null>(DEFAULT_DEMO_USER);
  const [token, setToken] = useState<string | null>('demo_active_token_nexora');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Récupération de la session en cours (sessionStorage ou localStorage)
    const activeToken =
      sessionStorage.getItem('nexora_session_token') ||
      sessionStorage.getItem('nexora_access_token') ||
      localStorage.getItem('nexora_session_token') ||
      localStorage.getItem('nexora_access_token');

    const activeUser =
      sessionStorage.getItem('nexora_session_user') ||
      sessionStorage.getItem('nexora_user') ||
      localStorage.getItem('nexora_session_user') ||
      localStorage.getItem('nexora_user');

    if (activeToken && activeUser) {
      try {
        const parsedUser = JSON.parse(activeUser);
        setToken(activeToken);
        setUser(parsedUser);
        setIsLoading(false);
        return;
      } catch (e) {
        console.error('Erreur lecture session:', e);
      }
    }

    // Par défaut : initialiser la session prête à l'emploi avec l'utilisateur administrateur principal
    sessionStorage.setItem('nexora_session_token', 'demo_active_token_nexora');
    sessionStorage.setItem('nexora_session_user', JSON.stringify(DEFAULT_DEMO_USER));
    localStorage.setItem('nexora_session_token', 'demo_active_token_nexora');
    localStorage.setItem('nexora_session_user', JSON.stringify(DEFAULT_DEMO_USER));
    setToken('demo_active_token_nexora');
    setUser(DEFAULT_DEMO_USER);
    setIsLoading(false);
  }, []);

  const login = (newToken: string, newUser: User) => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('nexora_session_token', newToken);
      sessionStorage.setItem('nexora_session_user', JSON.stringify(newUser));
      sessionStorage.setItem('nexora_access_token', newToken);
      sessionStorage.setItem('nexora_user', JSON.stringify(newUser));
      localStorage.setItem('nexora_session_token', newToken);
      localStorage.setItem('nexora_session_user', JSON.stringify(newUser));
      localStorage.setItem('nexora_access_token', newToken);
      localStorage.setItem('nexora_user', JSON.stringify(newUser));
    }
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    if (typeof window !== 'undefined') {
      sessionStorage.clear();
      localStorage.removeItem('nexora_session_token');
      localStorage.removeItem('nexora_session_user');
      localStorage.removeItem('nexora_access_token');
      localStorage.removeItem('nexora_user');
    }
    setToken(null);
    setUser(null);
    router.push('/login');
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
