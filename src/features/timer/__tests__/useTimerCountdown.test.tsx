// useTimerCountdown.test.tsx — Tests do hook countdown (RN-EJE-01)
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTimerCountdown } from '../../timer/domain/useTimerCountdown';



describe('useTimerCountdown', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('inicia con total segundos = minutos * 60', () => {
        const { result } = renderHook(() => useTimerCountdown(90));
        expect(result.current.remainingSeconds).toBe(5400);
    });

    it('muestra formato HH:MM:SS inicial', () => {
        const { result } = renderHook(() => useTimerCountdown(90));
        expect(result.current.displayFormat).toBe('01:30:00');
    });

    it('isUrgent es false con bastante tempo', () => {
        const { result } = renderHook(() => useTimerCountdown(90));
        expect(result.current.isUrgent).toBe(false);
    });

    it('stop detiene o countdown sen lanzar erros', () => {
        const { result, unmount } = renderHook(() => useTimerCountdown(90));
        expect(() => { result.current.stop(); }).not.toThrow();
        act(() => { result.current.stop(); });
        unmount();
    });

    it('countdown 0 minutos non falla', () => {
        const { result } = renderHook(() => useTimerCountdown(0));
        expect(result.current.remainingSeconds).toBe(0);
        expect(result.current.displayFormat).toBe('00:00:00');
    });

    it('countdown 1 minuto inicia correctamente', () => {
        const { result } = renderHook(() => useTimerCountdown(1));
        expect(result.current.remainingSeconds).toBe(60);
        expect(result.current.displayFormat).toBe('00:01:00');
    });
});
