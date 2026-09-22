'use client';

import * as React from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Camera, RefreshCw, AlertCircle, Barcode, CheckCircle2 } from 'lucide-react';

interface BarcodeScannerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScanSuccess: (decodedText: string) => void;
}

export function BarcodeScannerModal({
  isOpen,
  onClose,
  onScanSuccess,
}: BarcodeScannerModalProps) {
  const [scannerError, setScannerError] = React.useState<string | null>(null);
  const [isStarting, setIsStarting] = React.useState(false);
  const [manualCode, setManualCode] = React.useState('');
  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  const streamRef = React.useRef<MediaStream | null>(null);

  // Stop video stream
  const stopScanner = React.useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  // Pure native HTML5 WebRTC camera stream (100% dependency-free)
  const startScanner = React.useCallback(async () => {
    setScannerError(null);
    setIsStarting(true);

    try {
      stopScanner();

      if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error("L'accès direct à la caméra nécessite un navigateur récent et une connexion sécurisée (HTTPS ou localhost).");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
    } catch (err: any) {
      console.warn('Erreur accès caméra:', err);
      let msg = err.message || 'Impossible d\'activer la caméra.';
      if (err.name === 'NotAllowedError') {
        msg = 'Accès caméra refusé par le navigateur. Veuillez autoriser la webcam.';
      } else if (err.name === 'NotFoundError') {
        msg = 'Aucun capteur caméra détecté. Utilisez la saisie par douchette ou clavier.';
      }
      setScannerError(msg);
    } finally {
      setIsStarting(false);
    }
  }, [stopScanner]);

  React.useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        startScanner();
      }, 200);
      return () => clearTimeout(timer);
    } else {
      stopScanner();
      setManualCode('');
    }
  }, [isOpen, startScanner, stopScanner]);

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (manualCode.trim()) {
      onScanSuccess(manualCode.trim());
      stopScanner();
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        stopScanner();
        onClose();
      }}
      title="Scanner un Code-Barres / Entrée Optique"
      maxWidth="md"
    >
      <div className="space-y-4 pt-1">
        {/* Flux vidéo natif HTML5 pur (aucun package externe) */}
        <div className="relative w-full rounded-2xl overflow-hidden bg-black aspect-[4/3] flex items-center justify-center border border-border">
          <video
            ref={videoRef}
            playsInline
            muted
            className="w-full h-full object-cover"
          />

          {isStarting && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-xs flex flex-col items-center justify-center gap-2 text-foreground z-10">
              <RefreshCw className="h-8 w-8 text-primary animate-spin" />
              <p className="text-xs font-semibold">Initialisation du flux caméra...</p>
            </div>
          )}

          {scannerError && (
            <div className="absolute inset-0 bg-background/95 p-6 flex flex-col items-center justify-center text-center gap-3 z-10">
              <AlertCircle className="h-10 w-10 text-rose-500" />
              <p className="text-xs font-semibold text-rose-500 max-w-sm">{scannerError}</p>
              <Button size="sm" variant="outline" onClick={startScanner}>
                <RefreshCw className="h-4 w-4 mr-1.5" /> Réessayer la Caméra
              </Button>
            </div>
          )}
        </div>

        {/* Saisie rapide au clavier ou douchette code-barres USB */}
        <form onSubmit={handleManualSubmit} className="space-y-2 p-3 rounded-xl border bg-card">
          <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
            <Barcode className="h-4 w-4 text-primary" /> Saisir ou flasher à la douchette USB :
          </label>
          <div className="flex gap-2">
            <Input
              autoFocus
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              placeholder="Flashez le code ou tapez SKU (ex: LAPTOP-HP-01)..."
              className="text-xs font-mono"
            />
            <Button type="submit" size="sm" className="shrink-0 font-semibold">
              <CheckCircle2 className="h-4 w-4 mr-1" /> Valider
            </Button>
          </div>
        </form>

        <div className="flex justify-end pt-2 border-t border-border">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              stopScanner();
              onClose();
            }}
          >
            Fermer
          </Button>
        </div>
      </div>
    </Modal>
  );
}
