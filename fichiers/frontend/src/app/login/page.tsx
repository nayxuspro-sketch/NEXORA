'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Lock, Mail, ArrowRight, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = React.useState('admin@nexora-enterprise.com');
  const [password, setPassword] = React.useState('Admin123456!');
  const [errorMsg, setErrorMsg] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setIsLoading(true);

    const enteredEmail = email.trim().toLowerCase();
    const enteredPass = password.trim();

    try {
      // 1. Tenter la connexion en direct sur le serveur API Django
      const endpoints = ['/api/v1/auth/token/', 'http://127.0.0.1:8008/api/v1/auth/token/'];
      let res: Response | null = null;
      let text = '';

      for (const ep of endpoints) {
        try {
          res = await fetch(ep, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: enteredEmail, password: enteredPass }),
          });
          text = await res.text();
          if (res.ok) break;
        } catch {
          // Continuer sur endpoint suivant
        }
      }

      if (res && res.ok) {
        try {
          const data = JSON.parse(text);
          if (data.access && data.user) {
            login(data.access, data.user);
            router.push('/');
            return;
          }
        } catch {
          // parse error
        }
      }

      throw new Error('Connexion impossible : identifiants refuses par le serveur, ou serveur de donnees injoignable. Aucune connexion n\'a ete simulee. Verifiez que le backend est demarre (start-local.bat), puis reessayez.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Échec de connexion au serveur.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4 relative overflow-hidden">
      {/* Decorative background glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-primary/20 rounded-full blur-3xl pointer-events-none" />

      <Card className="w-full max-w-md shadow-2xl border-slate-700 bg-slate-800/90 backdrop-blur-md text-slate-100 z-10">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto w-12 h-12 rounded-xl bg-primary flex items-center justify-center text-white font-black text-2xl shadow-lg mb-3">
            N
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-white">
            Connexion à NEXORA
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Plateforme Commerciale & Caisse Enregistreuse (Burkina Faso / FCFA)
          </CardDescription>
        </CardHeader>

        <CardContent className="pt-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            {errorMsg && (
              <div className="p-3 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300 block">
                Adresse Email Professionnelle
              </label>
              <div className="relative">
                <Input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="nom@entreprise.bf"
                  className="bg-slate-900/80 border-slate-700 text-white pl-9 h-11"
                />
                <Mail className="h-4 w-4 text-slate-400 absolute left-3 top-3.5 pointer-events-none" />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300 block">
                Mot de Passe
              </label>
              <div className="relative">
                <Input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="bg-slate-900/80 border-slate-700 text-white pl-9 h-11"
                />
                <Lock className="h-4 w-4 text-slate-400 absolute left-3 top-3.5 pointer-events-none" />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-11 font-bold text-sm bg-primary hover:bg-primary/90 text-white shadow-lg mt-2"
              isLoading={isLoading}
            >
              Se Connecter à l'Espace <ArrowRight className="h-4 w-4 ml-1.5" />
            </Button>
          </form>

        </CardContent>

        <CardFooter className="justify-center border-t border-slate-700/60 py-3 text-center">
          <p className="text-[11px] text-slate-500">
            NEXORA Enterprise ERP • Sécurisé par jetons chiffrés JWT
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
