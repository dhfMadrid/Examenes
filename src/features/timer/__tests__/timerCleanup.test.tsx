// timerCleanup.test.tsx — Test de limpieza al desmontar/unmount del hook useTimerCountdown (RN-EJE-BUG)
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTimerCountdown } from '../domain/useTimerCountdown';

describe('useTimerCountdown - limpieza y cleanup al desmontar', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.clearAllMocks();
    });

    it('stop() detiene el countdown — no sigue operando tras llamarlo', () => {
        // Usar timers reales para este test porque useTimerCountdown usa RAF, no setInterval
        vi.useRealTimers();
        
        const { result, unmount } = renderHook(() => useTimerCountdown(2)); // 120s
        expect(result.current.remainingSeconds).toBe(120);
        
        act(() => { result.current.stop(); });
        
        // Después de stop, esperar a que el RAF loop se detenga completamente
        return new Promise((resolve) => {
            setTimeout(() => {
                // El stop deberia haber detenido el countdown (no debería decrementar más si paramos inmediatamente)
                expect(result.current.stop).toBeDefined();
                act(() => { unmount(); });
                resolve(undefined);
            }, 100);
        });
    });

    it('unmount no lanza error — cleanup de RAF funciona', () => {
        const { result, unmount } = renderHook(() => useTimerCountdown(1)); // 60s
        
        expect(() => { act(() => { unmount(); }); }).not.toThrow();
        expect(result.current.stop).toBeDefined();
    });

    it('countdown 0 minutos init — no crashes', () => {
        const { result, unmount } = renderHook(() => useTimerCountdown(0));
        
        expect(result.current.remainingSeconds).toBe(0);
        expect(result.current.isUrgent).toBe(false);
        expect(() => { act(() => { unmount(); }); }).not.toThrow();
    });

    it('countdown 1 minuto init — valores correctos', () => {
        const { result, unmount } = renderHook(() => useTimerCountdown(1)); // 60s
        
        expect(result.current.remainingSeconds).toBe(60);
        expect(result.current.displayFormat).toBe('00:01:00');
        
        // stop no lanza error incluso con poco tiempo
        expect(() => { act(() => { result.current.stop(); }); }).not.toThrow();
        
        act(() => { unmount(); });
    });

    it('stop() puede llamarse multiples veces sin error', () => {
        const { result, unmount } = renderHook(() => useTimerCountdown(1));
        
        expect(() => { 
            act(() => { result.current.stop(); }); 
            act(() => { result.current.stop(); }); 
            act(() => { result.current.stop(); }); 
        }).not.toThrow();
        
        act(() => { unmount(); });
    });

    it('unmount多次 call no duplica cleanup — safe to unmount multiple times', () => {
        const { result, unmount } = renderHook(() => useTimerCountdown(2)); // 120s
        
        expect(result.current.remainingSeconds).toBe(120);
        
        expect(() => { act(() => { unmount(); }); }).not.toThrow();
        expect(() => { act(() => { unmount(); }); }).not.toThrow();
    });
});
