import { describe, it, expect } from 'vitest';
import {
  esNIFValido,
  validarTransicionFSM,
  getEstadoColor,
  ExamState,
} from './scoringRules';

// ============================================================
// RN-COR-01 - Regra de transición de estado (RN-EST)
// ============================================================

describe('validarTransicionFSM', () => {
  it('NP -> INI es valida (RN-EST: alumno pulsa Aceptar)', () => {
    expect(validarTransicionFSM(ExamState.NO_PRESENTADO, ExamState.INICIADO)).toBe(true);
  });

  it('INI -> COMP es valida', () => {
    expect(validarTransicionFSM(ExamState.INICIADO, ExamState.COMPROBADO)).toBe(true);
  });

  it('INI -> FIN directos son validas (RN-EST)', () => {
    expect(validarTransicionFSM(ExamState.INICIADO, ExamState.FINALIZADO)).toBe(true);
  });

  it('COMP -> FIN es valida', () => {
    expect(validarTransicionFSM(ExamState.COMPROBADO, ExamState.FINALIZADO)).toBe(true);
  });

  it('NO valida: NP -> COMP (salta INI)', () => {
    expect(validarTransicionFSM(ExamState.NO_PRESENTADO, ExamState.COMPROBADO)).toBe(false);
  });

  it('NO valida: NP -> FIN', () => {
    expect(validarTransicionFSM(ExamState.NO_PRESENTADO, ExamState.FINALIZADO)).toBe(false);
  });

  it('NO valida: COMP -> INICIADO (revertir)', () => {
    expect(validarTransicionFSM(ExamState.COMPROBADO, ExamState.INICIADO)).toBe(false);
  });

  it('NO valida: FIN -> cualquier estado (terminal)', () => {
    expect(validarTransicionFSM(ExamState.FINALIZADO, ExamState.NO_PRESENTADO)).toBe(false);
  });

  it('Mismo estado es invalido', () => {
    expect(validarTransicionFSM(ExamState.NO_PRESENTADO, ExamState.NO_PRESENTADO)).toBe(false);
  });
});

describe('getEstadoColor', () => {
  it('NP devuelve Marron #8B4513', () => {
    expect(getEstadoColor(0)).toBe('#8B4513');
  });

  it('INICIADO devuelve Naranja #FF8C00', () => {
    expect(getEstadoColor(1)).toBe('#FF8C00');
  });

  it('COMP devuelve Azul #4682B4', () => {
    expect(getEstadoColor(2)).toBe('#4682B4');
  });

  it('FINALIZADO verde LimeGreen #32CD32', () => {
    expect(getEstadoColor(3)).toBe('#32CD32');
  });
});

describe('esNIFValido', () => {
  it('DNI valido 12345678A', () => {
    expect(esNIFValido('12345678A')).toBe(true);
  });

  it('Pasaporte X1234567A valido', () => {
    expect(esNIFValido('X1234567A')).toBe(true);
  });

  it('Invalid DNI (9 digitos)', () => {
    expect(esNIFValido('123456789A')).toBe(false);
  });

  it('Invalid formato (letra al inicio)', () => {
    expect(esNIFValido('A12345678')).toBe(false);
  });
});

describe('ExamState enum', () => {
  it('tiene los valores correctos segun RN-EST', () => {
    expect(ExamState.NO_PRESENTADO).toBe(0);
    expect(ExamState.INICIADO).toBe(1);
    expect(ExamState.COMPROBADO).toBe(2);
    expect(ExamState.FINALIZADO).toBe(3);
  });
});
