'use client';

import * as React from 'react';
import { useMutation } from '@tanstack/react-query';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { apiRequest } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import {
  Bot,
  Send,
  Sparkles,
  ShieldCheck,
  Lightbulb,
  Info,
  User as UserIcon,
  HelpCircle,
  AlertTriangle
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  explanation?: {
    data_source: string;
    timeframe: string;
    logic: string;
    limits: string;
  };
  metrics?: any;
  suggestions?: string[];
  role_blocked?: boolean;
}

export default function AIAssistantPage() {
  const { user } = useAuth();
  const [messages, setMessages] = React.useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: `Bonjour ${user?.first_name || ''} ! Je suis l'assistant d'intelligence opérationnelle de NEXORA. Je peux répondre à vos questions sur les ventes du jour, les risques de rupture de stock, les marges de rentabilité ou vous dresser une synthèse d'activité.`,
      suggestions: [
        "Combien ai-je vendu aujourd'hui ?",
        "Quels produits risquent de manquer ?",
        "Quels sont mes produits les plus rentables ?",
        "Résume mon activité.",
        "Quels produits sont dormants ?",
      ],
    },
  ]);
  const [inputQuestion, setInputQuestion] = React.useState('');
  const chatEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: async (question: string) => {
      return await apiRequest<any>('/ai/chat/', {
        method: 'POST',
        body: JSON.stringify({ question }),
      });
    },
    onSuccess: (data, variables) => {
      const aiReply: ChatMessage = {
        id: Math.random().toString(),
        sender: 'ai',
        text: data.answer || "J'ai traité votre requête.",
        explanation: data.explanation,
        metrics: data.metrics,
        suggestions: data.suggestions,
        role_blocked: data.role_blocked,
      };
      setMessages((prev) => [...prev, aiReply]);
    },
    onError: (err: any) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          sender: 'ai',
          text: `Désolé, une erreur est survenue : ${err.message || 'Serveur indisponible.'}`,
        },
      ]);
    },
  });

  const handleSend = (textToSend?: string) => {
    const q = textToSend || inputQuestion;
    if (!q.trim()) return;

    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      sender: 'user',
      text: q,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuestion('');
    chatMutation.mutate(q);
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-foreground flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" /> Assistant IA & Décision Opérationnelle
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Cycle : <span className="font-semibold text-primary">Comprendre → Anticiper → Recommander → Automatiser</span>
            </p>
          </div>
          <Badge variant="outline" className="flex items-center gap-1.5 text-xs py-1">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
            <span>RBAC Actif ({user?.role || 'ADMIN'})</span>
          </Badge>
        </div>

        {/* Chat Box */}
        <Card className="shadow-lg border-2 border-primary/20 flex flex-col h-[600px]">
          <CardHeader className="py-3 px-4 border-b bg-muted/20 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-foreground">NEXORA Copilot</p>
                <p className="text-[10px] text-muted-foreground">Explicabilité des données en temps réel</p>
              </div>
            </div>
            <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
              <Info className="h-3.5 w-3.5" /> Estimations indicatives basées sur l'ERP
            </div>
          </CardHeader>

          {/* Messages scroll area */}
          <CardContent className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.sender === 'ai' && (
                  <div className="h-8 w-8 rounded-full bg-primary/20 text-primary flex items-center justify-center shrink-0 mt-0.5">
                    <Bot className="h-4 w-4" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-3.5 text-xs sm:text-sm space-y-2 shadow-xs ${
                    msg.sender === 'user'
                      ? 'bg-primary text-primary-foreground rounded-tr-none'
                      : msg.role_blocked
                      ? 'bg-amber-500/10 border border-amber-500/30 text-amber-900 dark:text-amber-300 rounded-tl-none'
                      : 'bg-muted/60 border rounded-tl-none text-foreground'
                  }`}
                >
                  <p className="leading-relaxed whitespace-pre-line">{msg.text}</p>

                  {/* Explicabilité transparente de la recommandation / métrique */}
                  {msg.explanation && (
                    <div className="mt-3 pt-2.5 border-t border-border/60 text-[11px] space-y-1 bg-card/60 p-2.5 rounded-lg text-muted-foreground">
                      <p className="font-bold text-foreground flex items-center gap-1">
                        <Lightbulb className="h-3.5 w-3.5 text-amber-500" /> Cadre d'explicabilité :
                      </p>
                      <p><strong>Sources :</strong> {msg.explanation.data_source}</p>
                      <p><strong>Période :</strong> {msg.explanation.timeframe}</p>
                      <p><strong>Logique métier :</strong> {msg.explanation.logic}</p>
                      <p className="text-amber-700 dark:text-amber-400">
                        <strong>Limites & Hypothèses :</strong> {msg.explanation.limits}
                      </p>
                    </div>
                  )}

                  {/* Suggestions pills */}
                  {msg.suggestions && msg.suggestions.length > 0 && (
                    <div className="pt-2 flex flex-wrap gap-1.5">
                      {msg.suggestions.map((sug, i) => (
                        <button
                          key={i}
                          onClick={() => handleSend(sug)}
                          className="px-2.5 py-1 rounded-full bg-card hover:bg-primary hover:text-primary-foreground border text-[11px] font-medium transition-all shadow-2xs"
                        >
                          {sug}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {msg.sender === 'user' && (
                  <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold">
                    {user?.first_name?.[0] || 'U'}
                  </div>
                )}
              </div>
            ))}

            {chatMutation.isPending && (
              <div className="flex gap-3 items-center text-xs text-muted-foreground animate-pulse">
                <div className="h-8 w-8 rounded-full bg-primary/20 text-primary flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <span>Analyse des données opérationnelles en cours...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </CardContent>

          {/* Input Footer */}
          <CardFooter className="p-3 border-t bg-card flex gap-2">
            <Input
              placeholder="Posez votre question (ex: Quels produits risquent de manquer ?)"
              value={inputQuestion}
              onChange={(e) => setInputQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              className="text-xs sm:text-sm h-11"
            />
            <Button
              className="h-11 px-4"
              disabled={!inputQuestion.trim() || chatMutation.isPending}
              onClick={() => handleSend()}
            >
              <Send className="h-4 w-4" />
            </Button>
          </CardFooter>
        </Card>
      </div>
    </DashboardLayout>
  );
}
