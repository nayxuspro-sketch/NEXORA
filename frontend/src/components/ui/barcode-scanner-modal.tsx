'use client';

import * as React from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Camera, RefreshCw, AlertCircle, Barcode, CheckCircle2, SwitchCamera, Video } from 'lucide-react';

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
  const [hasCameraStream, setHasCameraStream] = React.useState(false);
  const [manualCode, setManualCode] = React.useState('');
  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  const streamRef = React.useRef<MediaStream | null>(null);
  const scannerInstanceRef = React.useRef<any>(null);
  const readerElementId = 'nexora-interactive-barcode-reader';

  // Stop media stream and cleanup
  const stopScanner = React.useCallback(async () => {
    if (scannerInstanceRef.current) {
      try {
        if (scannerInstanceRef.current.isScanning) {
          await scannerInstanceRef.current.stop();
        }
        await scannerInstanceRef.current.clear();
      } catch (err) {
        console.warn('Erreur lors de l\'arrêt du scanner:', err);
      } finally {
        scannerInstanceRef.current = null;
      }
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setHasCameraStream(false);
  }, []);

  // Start scanner: dynamically import html5-qrcode if available, or fallback gracefully to native WebRTC video
  const startScanner = React.useCallback(async () => {
    setScannerError(null);
    setIsStarting(true);

    try {
      await stopScanner();

      // Check browser getUserMedia support
      if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error('Votre navigateur ne supporte pas l\'accès direct à la caméra ou le contexte n\'est pas sécurisé (HTTPS ou localhost requis).');
      }

      // Try dynamic import of html5-qrcode
      let html5QrcodeModule: any = null;
      try {
        html5QrcodeModule = await import('html5-qrcode');
      } catch (importErr) {
        console.warn('html5-qrcode non disponible, utilisation du flux vidéo standard:', importErr);
      }

      if (html5QrcodeModule && html5QrcodeModule.Html5Qrcode) {
        const { Html5Qrcode, Html5QrcodeSupportedFormats } = html5QrcodeModule;
        const devices = await Html5Qrcode.getCameras();
        if (!devices || devices.length === 0) {
          throw new Error('Aucune caméra ou webcam détectée sur cet appareil.');
        }

        const backCamera = devices.find((d: any) =>
          d.label?.toLowerCase().includes('back') ||
          d.label?.toLowerCase().includes('arrière') ||
          d.label?.toLowerCase().includes('environment')
        );
        const targetId = backCamera ? backCamera.id : devices[0].id;

        const scanner = new Html5Qrcode(readerElementId, {
          formatsToSupport: [
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.QR_CODE,
          ],
          verbose: false,
        });

        scannerInstanceRef.current = scanner;

        await scanner.start(
          targetId,
          { fps: 15, qrbox: { width: 260, height: 160 }, aspectRatio: 1.333333 },
          (decodedText: string) => {
            onScanSuccess(decodedText);
            stopScanner();
            onClose();
          },
          () => {}
        );
        setHasCameraStream(true);
      } else {
        // Fallback: Native WebRTC Video Stream
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } }
        });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setHasCameraStream(true);
      }
    } catch (err: any) {
      console.error('Erreur caméra:', err);
      let msg = err.message || 'Impossible d\'accéder à la caméra.';
      if (err.name === 'NotAllowedError' || msg.includes('Permission')) {
        msg = 'Permission caméra refusée. Veuillez autoriser l\'accès dans les paramètres du navigateur.';
      } else if (err.name === 'NotFoundError') {
        msg = 'Aucun capteur vidéo/caméra détecté.';
      }
      setScannerError(msg);
    } finally {
      setIsStarting(false);
    }
  }, [onClose, onScanSuccess, stopScanner]);

  React.useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        startScanner();
      }, 250);
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
        {/* Camera viewport container */}
        <div className="relative w-full rounded-2xl overflow-hidden bg-black aspect-[4/3] flex items-center justify-center border border-border">
          <div id={readerElementId} className="w-full h-full" />
          <video
            ref={videoRef}
            playsInline
            muted
            className="w-full h-full object-cover"
            style={{ display: scannerInstanceRef.current ? 'none' : 'block' }}
          />

          {isStarting && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-xs flex flex-col items-center justify-center gap-2 text-foreground z-10">
              <RefreshCw className="h-8 w-8 text-primary animate-spin" />
              <p className="text-xs font-semibold">Initialisation de la caméra...</p>
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

        {/* Alternative: Saisie manuelle immédiate si pas de caméra */}
        <form onSubmit={handleManualSubmit} className="space-y-2 p-3 rounded-xl border bg-card">
          <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
            <Barcode className="h-4 w-4 text-primary" /> Ou saisir / scanner avec douchette USB :
          </label>
          <div className="flex gap-2">
            <Input
              autoFocus
              value={manualCode}
              onChange={(e) => setManualCode(e.target.value)}
              placeholder="Code-barres EAN-13, SKU..."
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
