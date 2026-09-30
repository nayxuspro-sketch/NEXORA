'use client';

import * as React from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Camera, RefreshCw, AlertCircle, Barcode, CheckCircle2, Zap } from 'lucide-react';

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
  const [isScanningActive, setIsScanningActive] = React.useState(false);
  const [detectedFeedback, setDetectedFeedback] = React.useState<string | null>(null);

  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);
  const streamRef = React.useRef<MediaStream | null>(null);
  const animationFrameRef = React.useRef<number | null>(null);
  const isDecodingRef = React.useRef<boolean>(false);

  // Play audio beep upon barcode detection
  const playBeep = () => {
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.12);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.12);
    } catch {}
  };

  // Stop video stream & loop
  const stopScanner = React.useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsScanningActive(false);
  }, []);

  // Frame processing loop for barcode detection
  const processFrame = React.useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !streamRef.current) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (video.readyState === video.HAVE_ENOUGH_DATA && !isDecodingRef.current) {
      // Setup canvas dimensions
      if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
      }

      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Native Browser BarcodeDetector API (Chrome, Edge, Opera, Android Webview)
        if ('BarcodeDetector' in window) {
          isDecodingRef.current = true;
          try {
            const BarcodeDetectorClass = (window as any).BarcodeDetector;
            const detector = new BarcodeDetectorClass({
              formats: [
                'ean_13',
                'ean_8',
                'code_128',
                'code_39',
                'upc_a',
                'upc_e',
                'qr_code',
                'itf',
              ],
            });

            detector
              .detect(video)
              .then((barcodes: any[]) => {
                if (barcodes && barcodes.length > 0) {
                  const rawValue = barcodes[0].rawValue;
                  if (rawValue && rawValue.trim()) {
                    setDetectedFeedback(rawValue.trim());
                    playBeep();
                    setTimeout(() => {
                      onScanSuccess(rawValue.trim());
                      stopScanner();
                      onClose();
                    }, 200);
                    return;
                  }
                }
                isDecodingRef.current = false;
              })
              .catch(() => {
                isDecodingRef.current = false;
              });
          } catch {
            isDecodingRef.current = false;
          }
        }
      }
    }

    animationFrameRef.current = requestAnimationFrame(processFrame);
  }, [onClose, onScanSuccess, stopScanner]);

  // Start webcam
  const startScanner = React.useCallback(async () => {
    setScannerError(null);
    setIsStarting(true);
    setDetectedFeedback(null);

    try {
      stopScanner();

      if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error("L'accès à la caméra nécessite HTTPS ou localhost.");
      }

      // Request high resolution for barcode readability
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: 'environment' },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setIsScanningActive(true);
        animationFrameRef.current = requestAnimationFrame(processFrame);
      }
    } catch (err: any) {
      console.warn('Erreur caméra:', err);
      let msg = err.message || 'Impossible d\'activer la caméra.';
      if (err.name === 'NotAllowedError') {
        msg = 'Permission caméra refusée. Autorisez la webcam dans le navigateur.';
      }
      setScannerError(msg);
    } finally {
      setIsStarting(false);
    }
  }, [processFrame, stopScanner]);

  React.useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        startScanner();
      }, 200);
      return () => clearTimeout(timer);
    } else {
      stopScanner();
      setManualCode('');
      setDetectedFeedback(null);
    }
  }, [isOpen, startScanner, stopScanner]);

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (manualCode.trim()) {
      playBeep();
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
        {/* Viewport vidéo avec cadre de visée et analyse d'image en direct */}
        <div className="relative w-full rounded-2xl overflow-hidden bg-black aspect-[4/3] flex items-center justify-center border border-border">
          <video
            ref={videoRef}
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          {/* Canvas caché servant à l'analyse d'image en mémoire */}
          <canvas ref={canvasRef} className="hidden" />

          {/* Viseur optique centré avec guide laser rouge */}
          {isScanningActive && (
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
              <div className="relative w-64 h-36 border-2 border-primary/80 rounded-xl bg-primary/5 flex items-center justify-center shadow-[0_0_20px_rgba(2,132,199,0.3)]">
                {/* Ligne laser horizontale rouge animée */}
                <div className="absolute w-full h-0.5 bg-rose-500 shadow-[0_0_8px_#f43f5e] animate-pulse" />
                <span className="text-[10px] font-bold text-white bg-black/60 px-2 py-0.5 rounded-full absolute -bottom-6">
                  Placez les barres dans le cadre
                </span>
              </div>
            </div>
          )}

          {/* Feedback lors de la détection réussie */}
          {detectedFeedback && (
            <div className="absolute inset-0 bg-emerald-600/80 backdrop-blur-xs flex flex-col items-center justify-center gap-2 text-white z-20 animate-fade-in">
              <CheckCircle2 className="h-12 w-12" />
              <p className="font-extrabold text-sm">Code Détecté : {detectedFeedback}</p>
            </div>
          )}

          {isStarting && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-xs flex flex-col items-center justify-center gap-2 text-foreground z-10">
              <RefreshCw className="h-8 w-8 text-primary animate-spin" />
              <p className="text-xs font-semibold">Initialisation de l'analyseur optique...</p>
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

        {/* Option 2 : Flash direct par douchette USB ou saisie rapide au clavier */}
        <form onSubmit={handleManualSubmit} className="space-y-2 p-3.5 rounded-xl border bg-muted/20">
          <label className="text-xs font-bold text-foreground flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Barcode className="h-4 w-4 text-primary" /> Saisie manuelle ou Flash Douchette USB :
            </span>
            <span className="text-[10px] text-muted-foreground font-normal">Touche Entrée pour valider</span>
          </label>
          <div className="flex gap-2">
            <Input
              autoFocus
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              placeholder="Flashez le code-barres ou tapez le SKU..."
              className="text-xs font-mono font-bold bg-background"
            />
            <Button type="submit" size="sm" className="shrink-0 font-bold px-4">
              <Zap className="h-3.5 w-3.5 mr-1" /> Valider
            </Button>
          </div>
          <p className="text-[11px] text-muted-foreground">
            Conseil : Sur un PC avec webcam standard (souvent à mise au point fixe), tenez le code-barres à <strong>15–20 cm</strong> bien éclairé, ou utilisez directement une douchette USB.
          </p>
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
