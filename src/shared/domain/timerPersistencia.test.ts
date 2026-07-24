// timerPersistencia.test.ts — Test do calculo temporal real (RN-EJE-01) con persistencia en memoria
import { describe, it, expect } from 'vitest';
import { calcularRestanteReal } from '@domain/timer.domain';

describe('calcularRestanteReal (persistencia de tempo real)', () => {
    // Simulado: 90min = 5400s como no sistema actual.

    it('Inicio con 5400s e decorrido 0s → 5400 restantes', () => {
        const agora = Date.now();
        const r = calcularRestanteReal(5400, agora);
        expect(r.restanteSegundos).toBeGreaterThanOrEqual(5399);
        expect(r.restanteSegundos).toBeLessThanOrEqual(5400);
        expect(r.expirado).toBe(false);
    });

    it('Inicio despois de 120s → restan ~5280s', () => {
        const inicio = Date.now() - 120_000; // hai 2 min
        const r = calcularRestanteReal(5400, inicio);
        expect(r.restanteSegundos).toBeGreaterThanOrEqual(5279);
        expect(r.restanteSegundos).toBeLessThanOrEqual(5281);
    });

    it('Despois da duración total → expirado=true', () => {
        const inicio = Date.now() - 6_000_100; // máis de 90 min
        const r = calcularRestanteReal(5400, inicio);
        expect(r.restanteSegundos).toBe(0);
        expect(r.expirado).toBe(true);
    });

    it('Duración curta (300s) e a medio camiño → non expirado', () => {
        const inicio = Date.now() - 150_000; // hai 150s
        const r = calcularRestanteReal(300, inicio);
        expect(r.restanteSegundos).toBeGreaterThanOrEqual(149);
        expect(r.restanteSegundos).toBeLessThanOrEqual(151);
    });

    it('Exactamente na duración → 0', () => {
        const r = calcularRestanteReal(300, Date.now() - 300_000); // fai exactamente 300s
        expect(r.restanteSegundos).toBeLessThanOrEqual(1);
    });

    it('Duración 60min, decorrido 59min50s → 10 restantes', () => {
        const inicio = Date.now() - (59 * 60 + 50) * 1000;
        const r = calcularRestanteReal(3600, inicio); // 60 min
        expect(r.restanteSegundos).toBeGreaterThanOrEqual(8);
        expect(r.restanteSegundos).toBeLessThanOrEqual(12); // ±2s por precisión
    });
});
