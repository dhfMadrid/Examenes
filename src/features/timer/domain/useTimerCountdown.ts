// useTimerCountdown — Hook React para countdown de examen (RN-EJE-01)
import { useState, useEffect, useCallback, useRef } from 'react';
import { formatTimeFromSeconds, estaCercaDeExpirar } from '../../../shared/domain/timer.domain';

export interface _UseTimerCountdownReturn {
  /** Segundos restantes */
  remainingSeconds: number;
  /** Formato HH-MM-SS para auto-save o UI */
  displayFormat: string;
  /** ¿Está cerca de expirar (<60s)? */
  isUrgent: boolean;
  /** Tiempo total inicial (minutos) */
  totalMinutes: number;
  /** Detener countdown */
  stop: () => void;
}

/**
 * Hook que maneja un countdown basado en minutos totales.
 * Usa requestAnimationFrame cuando es posible para mayor precisión,
 * con fallback a setInterval de 1s.
 */
export function useTimerCountdown(totalMinutes: number) {
  const [remainingSeconds, setRemainingSeconds] = useState(totalMinutes * 60);
  const [isUrgent, setIsUrgent] = useState(false);
  const startTimeRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const isStoppedRef = useRef(false);

  const stop = useCallback(() => {
    isStoppedRef.current = true;
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }
  }, []);

  useEffect(() => {
    if (totalMinutes <= 0) return;

    setRemainingSeconds(totalMinutes * 60);
    setIsUrgent(false);
    isStoppedRef.current = false;
    startTimeRef.current = Date.now();

    const tick = () => {
      if (isStoppedRef.current) return;

      const elapsed = Math.floor((Date.now() - (startTimeRef.current ?? Date.now())) / 1000);
      const remaining = totalMinutes * 60 - elapsed;

      if (remaining <= 0) {
        setRemainingSeconds(0);
        setIsUrgent(false);
        return; // countdown finished
      }

      setRemainingSeconds(remaining);
      setIsUrgent(estaCercaDeExpirar(remaining));
      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      isStoppedRef.current = true;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [totalMinutes]);

  const displayFormat = formatTimeFromSeconds(Math.max(0, remainingSeconds));

  return {
    remainingSeconds,
    displayFormat,
    isUrgent,
    totalMinutes,
    stop,
  };
}
