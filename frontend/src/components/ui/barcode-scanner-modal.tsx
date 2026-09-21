'use client';

import * as React from 'react';
import { Modal } from '@/components/ui/modal';
import { Button } from '@/components/ui/button';
import { Camera, RefreshCw, AlertCircle, CheckCircle2, SwitchCamera } from 'lucide-react';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';

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
  const [cameras, setCameras] = React.useState<Array<{ id: string; label: string }>>([]);
  const [selectedCameraId, setSelectedCameraId] = React.useState<string | null>(null);
  const scannerRef = React.useRef<Html5Qrcode | null>(null);
  const readerElementId = 'nexora-interactive-barcode-reader';

  // Stop scanner safely
  const stopScanner = React.useCallback(async () => {
    if (scannerRef.current) {
      try {
        if (scannerRef.current.isScanning) {
          await scannerRef.current.stop();
        }
        await scannerRef.current.clear();
      } catch (err) {
        console.warn('Erreur lors de l\'arrêt de la caméra:', err);
      } finally {
        scannerRef.current = null;
      }
    }
  }, []);

  // Start scanner
  const startScanner = React.useCallback(async (cameraId?: string) => {
    setScannerError(null);
    setIsStarting(true);

    try {
      // Ensure previous scanner instance stopped
      await stopScanner();

      // Check browser getUserMedia support
      if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error('Votre navigateur ne supporte pas l\'accès direct à la caméra ou le contexte n\'est pas sécurisé (HTTPS / localhost requis).');
      }

      // Enumerate cameras
      const devices = await Html5Qrcode.getCameras();
      if (!devices || devices.length === 0) {
        throw new Error('Aucune caméra ou webcam détectée sur cet appareil.');
      }

      setCameras(devices);

      // Select camera: back camera for mobile/tablet if available, or first device
      let targetCameraId = cameraId;
      if (!targetCameraId) {
        const backCamera = devices.find((d) =>
          d.label.toLowerCase().includes('back') ||
          d.label.toLowerCase().includes('arrière') ||
          d.label.toLowerCase().includes('environment')
        );
        targetCameraId = backCamera ? backCamera.id : devices[0].id;
      }
      setSelectedCameraId(targetCameraId);

      // Create new Html5Qrcode instance
      const html5QrCode = new Html5Qrcode(readerElementId, {
        formatsToSupport: [
          Html5QrcodeSupportedFormats.EAN_13,
          Html5QrcodeSupportedFormats.EAN_8,
          Html5QrcodeSupportedFormats.CODE_128,
          Html5QrcodeSupportedFormats.CODE_39,
          Html5QrcodeSupportedFormats.UPC_A,
          Html5QrcodeSupportedFormats.UPC_E,
          Html5QrcodeSupportedFormats.QR_CODE,
          Html5QrcodeSupportedFormats.ITF,
        ],
        verbose: false,
      });

      scannerRef.current = html5QrCode;

      const config = {
        fps: 15,
        qrbox: { width: 260, height: 160 },
        aspectRatio: 1.333333,
      };

      await html5QrCode.start(
        targetCameraId,
        config,
        (decodedText) => {
          // Play audio beep if possible
          try {
            const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
            const osc = ctx.createOscillator();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime);
            osc.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.1);
          } catch (e) {
            // Audio context not allowed or failed
          }

          onScanSuccess(decodedText);
          stopScanner();
          onClose();
        },
        () => {
          // ignore frame scan errors (normal when no code in view)
        }
      );
    } catch (err: any) {
      console.error('Camera Scanner start error:', err);
      let msg = err.message || 'Impossible d\'accéder à la caméra.';
      if (err.name === 'NotAllowedError' || msg.includes('Permission')) {
        msg = 'Permission caméra refusée. Veuillez autoriser l\'accès à la caméra dans les paramètres de votre navigateur.';
      } else if (err.name === 'NotFoundError') {
        msg = 'Aucun capteur caméra trouvé sur cet appareil.';
      } else if (err.name === 'NotReadableError') {
        msg = 'La caméra est déjà utilisée par une autre application ou un autre onglet.';
      }
      setScannerError(msg);
    } finally {
      setIsStarting(false);
    }
  }, [onClose, onScanSuccess, stopScanner]);

  // When modal opens/closes
  React.useEffect(() => {
    if (isOpen) {
      // Delay slightly for DOM element mounting
      const timer = setTimeout(() => {
        startScanner();
      }, 250);
      return () => clearTimeout(timer);
    } else {
      stopScanner();
    }
  }, [isOpen, startScanner, stopScanner]);

  // Switch camera handler
  const handleSwitchCamera = () => {
    if (cameras.length <= 1) return;
    const currentIndex = cameras.findIndex((c) => c.id === selectedCameraId);
    const nextIndex = (currentIndex + 1) % cameras.length;
    const nextCamera = cameras[nextIndex];
    setSelectedCameraId(nextCamera.id);
    startScanner(nextCamera.id);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        stopScanner();
        onClose();
      }}
      title="Scanner un Code-Barres / QR Code via Caméra"
      maxWidth="md"
    >
      <div className="space-y-4 pt-1">
        {/* Camera viewport container */}
        <div className="relative w-full rounded-2xl overflow-hidden bg-black aspect-[4/3] flex items-center justify-center border border-border">
          <div id={readerElementId} className="w-full h-full" />

          {isStarting && (
            <div className="absolute inset-0 bg-background/80 backdrop-blur-xs flex flex-col items-center justify-center gap-2 text-foreground">
              <RefreshCw className="h-8 w-8 text-primary animate-spin" />
              <p className="text-xs font-semibold">Démarrage du flux vidéo de la caméra...</p>
            </div>
          )}

          {scannerError && (
            <div className="absolute inset-0 bg-background/95 p-6 flex flex-col items-center justify-center text-center gap-3">
              <AlertCircle className="h-10 w-10 text-rose-500" />
              <p className="text-xs font-semibold text-rose-500 max-w-sm">{scannerError}</p>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => startScanner(selectedCameraId || undefined)}>
                  <RefreshCw className="h-4 w-4 mr-1.5" /> Réessayer
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Controls & instructions */}
        <div className="flex items-center justify-between text-xs text-muted-foreground px-1">
          <span>Pointez la caméra vers le code-barres (EAN-13, EAN-8, QR Code, Code 128)</span>
          {cameras.length > 1 && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleSwitchCamera}
              className="h-8 text-xs shrink-0"
              title="Changer de caméra (avant / arrière)"
            >
              <SwitchCamera className="h-3.5 w-3.5 mr-1" /> Changer ({cameras.length})
            </Button>
          )}
        </div>

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
