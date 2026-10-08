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

// NOTE : aucune session de demonstration. L'acces aux donnees exige un vrai
// jeton emis par le serveur (voir ci-dessous).

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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

    // Un jeton de demonstration ne vaut rien : le serveur le refuse.
    const jetonUtilisable = !!activeToken && activeToken.startsWith('eyJ');

    if (jetonUtilisable && activeUser) {
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

    // Aucune session utilisable : on ne simule rien. La garde des routes
    // conduit a la page de connexion, ou l'utilisateur s'authentifie vraiment.
    if (activeToken && !jetonUtilisable) {
      sessionStorage.removeItem('nexora_session_token');
      sessionStorage.removeItem('nexora_session_user');
      localStorage.removeItem('nexora_session_token');
      localStorage.removeItem('nexora_session_user');
    }
    setToken(null);
    setUser(null);
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
