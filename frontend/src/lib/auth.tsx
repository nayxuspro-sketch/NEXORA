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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Authentification stricte de session :
  // A chaque lancement ou nouvelle ouverture du navigateur, sessionStorage est vide,
  // ce qui force immédiatement l'affichage de la page de connexion (/login).
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // Récupération exclusive en session active
    const activeToken = sessionStorage.getItem('nexora_session_token') || sessionStorage.getItem('nexora_access_token');
    const activeUser = sessionStorage.getItem('nexora_session_user') || sessionStorage.getItem('nexora_user');

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

    // Si aucune session active n'est trouvée (nouveau lancement de l'application),
    // réinitialisation complète et redirection obligatoire vers /login
    setToken(null);
    setUser(null);
    setIsLoading(false);

    if (pathname !== '/login') {
      router.push('/login');
    }
  }, [pathname, router]);

  const login = (newToken: string, newUser: User) => {
    if (typeof window !== 'undefined') {
      // Stocker en sessionStorage (dure uniquement le temps de la session du navigateur)
      sessionStorage.setItem('nexora_session_token', newToken);
      sessionStorage.setItem('nexora_session_user', JSON.stringify(newUser));
      // Mirroring pour rétrocompatibilité
      sessionStorage.setItem('nexora_access_token', newToken);
      sessionStorage.setItem('nexora_user', JSON.stringify(newUser));
      // Nettoyer d'éventuels résidus permanents pour éviter tout contournement
      localStorage.removeItem('nexora_access_token');
      localStorage.removeItem('nexora_user');
    }
    setToken(newToken);
    setUser(newUser);
  };

  const logout = () => {
    if (typeof window !== 'undefined') {
      sessionStorage.clear();
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
