// timer.domain.test.ts — RN-EJE-01, RN-EJE-02, RN-EJE-04: tests de dominio do cronómetro

import { describe, it, expect } from 'vitest';
import {
  formatTimeFromSeconds,
  formatTimeDisplay,
  calcularRestante,
  estaExpirado,
  dividirModulo13,
  estaCercaDeExpirar,
  REVISION_TIME_SECONDS,
} from './timer.domain';

// ============================================================
// RN-EJE-01: Formateo de tempo do countdown
// O sistema antigo mostra HH:MM:SS con separador '-' no auto-save e HH:MM no UI
// ============================================================

describe('formatTimeFromSeconds (RN-EJE-01)', () => {
    it('0 segundos → "00:00:00"', () => {
        expect(formatTimeFromSeconds(0)).toBe('00:00:00');
    });

    it('59 segundos → "00:00:59"', () => {
        expect(formatTimeFromSeconds(59)).toBe('00:00:59');
    });

    it('60 segundos → "00:01:00"', () => {
        expect(formatTimeFromSeconds(60)).toBe('00:01:00');
    });

    it('3600 segundos (1 hora) → "01:00:00"', () => {
        expect(formatTimeFromSeconds(3600)).toBe('01:00:00');
    });

    it('5400 secondi (90 min) → "01:30:00" (TTest típico)', () => {
        expect(formatTimeFromSeconds(5400)).toBe('01:30:00');
    });

    it('valores negativos tratados como 0', () => {
        expect(formatTimeFromSeconds(-5)).toBe('00:00:00');
    });

    it('9h 59min 59s → "09:59:59"', () => {
        expect(formatTimeFromSeconds(9 * 3600 + 59 * 60 + 59)).toBe('09:59:59');
    });

    it('120min → "02:00:00" (Examen grande)', () => {
        expect(formatTimeFromSeconds(7200)).toBe('02:00:00');
    });
});

describe('formatTimeDisplay (UI countdown display)', () => {
    it('90 min → "01:30"', () => {
        expect(formatTimeDisplay(5400)).toBe('01:30');
    });

    it('60s → "00:01"', () => {
        expect(formatTimeDisplay(60)).toBe('00:01');
    });

    it('negativo → "00:00"', () => {
        expect(formatTimeDisplay(-1)).toBe('00:00');
    });

    it('9h → "09:00"', () => {
        expect(formatTimeDisplay(9 * 3600)).toBe('09:00');
    });
});

// ============================================================
// RN-EJE-01: Cálculo do tempo restante (countdown real)
// ============================================================

describe('calcularRestante (RN-EJE-01)', () => {
    it('sen decorrer tempo → total completo', () => {
        expect(calcularRestante(90, 0)).toBe(5400); // 90min * 60s
    });

    it('1 minuto decorrido de 90min → 89min restantes', () => {
        expect(calcularRestante(90, 60000)).toBe(5340);
    });

    it('2700s (half of 90min) → exactly half remaining', () => {
        expect(calcularRestante(90, 2700000)).toBe(2700);
    });

    it('cando decorrido > total → 0', () => {
        expect(calcularRestante(90, 5400001)).toBe(0);
    });

    it('1 second remaining → 0 (floor)', () => {
        expect(calcularRestante(90, 5399200)).toBe(0); // 800ms left floors to 0
    });

    it('exactly at expiry → 0', () => {
        expect(calcularRestante(90, 5400000)).toBe(0);
    });
});

describe('estaExpirado (RN-EJE-01)', () => {
    it('zero decorrido → false', () => {
        expect(estaExpirado(90, 0)).toBe(false);
    });

    it('a medio camiño → false', () => {
        expect(estaExpirado(90, 2000000)).toBe(false);
    });

    it('ao acabar → true', () => {
        expect(estaExpirado(90, 5400000)).toBe(true);
    });

    it('despois de expirar → true', () => {
        expect(estaExpirado(90, 6000000)).toBe(true);
    });

    it('1 segundo antes de expirar → false', () => {
        expect(estaExpirado(90, 5398999)).toBe(false);
    });
});

// ============================================================
// RN-EJE-02: División automática do módulo 13 en dúas partes
// Cada parte = TTest/2 minutos máis 30 segundos adicionais
// ============================================================

describe('RN-EJE-02: dividirModulo13', () => {
    it('TTest=180min → cada parte = 90min + 30s (5430s)', () => {
        const r = dividirModulo13(180);
        expect(r.parte1TempoSeg).toBe(5430);
        expect(r.parte2TempoSeg).toBe(5430);
    });

    it('TTest=120min → cada parte = 60min + 30s (3630s)', () => {
        const r = dividirModulo13(120);
        expect(r.parte1TempoSeg).toBe(3630);
        expect(r.parte2TempoSeg).toBe(3630);
    });

    it('TTest=90min → cada parte = 45min + 30s (2730s)', () => {
        const r = dividirModulo13(90);
        expect(r.parte1TempoSeg).toBe(2730);
        expect(r.parte2TempoSeg).toBe(2730);
    });

    it('TTest=60min → cada parte = 30min + 30s (1830s)', () => {
        const r = dividirModulo13(60);
        expect(r.parte1TempoSeg).toBe(1830);
        expect(r.parte2TempoSeg).toBe(1830);
    });

    it('Total das dúas partes = TTest * 60 + 60 (engade 1min extra pola suma dos 30s)', () => {
        const r = dividirModulo13(180);
        const totalSeg = r.parte1TempoSeg + r.parte2TempoSeg;
        // (90*60+30) * 2 = 5430 * 2 = 10860s = 181 minutos
        expect(totalSeg).toBe(10860);
        expect(totalSeg / 60).toBe(181); // +1 min porque hai dous "30s" extras
    });

    it('TTest=1min → cada parte = 0min + 30s = 30s', () => {
        const r = dividirModulo13(1);
        expect(r.parte1TempoSeg).toBe(30);
        expect(r.parte2TempoSeg).toBe(30);
    });

    it('TTest=3min → cada parte = 1min + 30s = 90s', () => {
        const r = dividirModulo13(3);
        expect(r.parte1TempoSeg).toBe(90);
        expect(r.parte2TempoSeg).toBe(90);
    });
});

// ============================================================
// RN-EJE-04: Comprobacións de cor e revisión
// ============================================================

describe('estaCercaDeExpirar (RN-EJE-01 cor vermella)', () => {
    it('59 segundos → true (<60s)', () => {
        expect(estaCercaDeExpirar(59)).toBe(true);
    });

    it('60 segundos → false (non é <60)', () => {
        expect(estaCercaDeExpirar(60)).toBe(false);
    });

    it('1 segundo → true', () => {
        expect(estaCercaDeExpirar(1)).toBe(true);
    });

    it('0 segundos → false (zero non se conta)' , () => {
        expect(estaCercaDeExpirar(0)).toBe(false);
    });

    it('5 minutos restantes → false', () => {
        expect(estaCercaDeExpirar(300)).toBe(false);
    });
});

describe('RN-EJE-04: tempo de revisión post-submit', () => {
    it('é exactamente 300 segundos (5 min)', () => {
        expect(REVISION_TIME_SECONDS).toBe(300);
    });
});
