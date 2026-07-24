import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ExamCard } from '../ExamCard';
import { ExamState } from '../../../../shared/domain/scoringRules';

describe('ExamCard - Estado del Examen (RN-EST-01)', () => {
  it('RN-EST-01a: NP renders con color #8B4513 y label "NO PRESENTADO"', () => {
    const examData = {
      id: 'exam-001',
      estado: ExamState.NO_PRESENTADO,
      modulo: '010 - AIR LAW',
      titulo: 'Examen Ley Aerea',
    };

    render(<ExamCard exam={examData} />);

    expect(screen.getByText('NO PRESENTADO')).toBeInTheDocument();
  });

  it('RN-EST-01b: INICIADO renders con color #FF8C00 y label "INICIADO"', () => {
    const examData = {
      id: 'exam-002',
      estado: ExamState.INICIADO,
      modulo: '030 - PERFLIGHT',
      titulo: 'Examen Perflight',
    };

    render(<ExamCard exam={examData} />);

    expect(screen.getByText('INICIADO')).toBeInTheDocument();
  });

  it('RN-EST-01c: COMPROBADO renders con color #4682B4 y label "COMPROBADO"', () => {
    const examData = {
      id: 'exam-003',
      estado: ExamState.COMPROBADO,
      modulo: '050 - RACES',
      titulo: 'Examen RACES',
    };

    render(<ExamCard exam={examData} />);

    expect(screen.getByText('COMPROBADO')).toBeInTheDocument();
  });

  it('RN-EST-01d: FINALIZADO renders con color #32CD32 y label "FINALIZADO"', () => {
    const examData = {
      id: 'exam-004',
      estado: ExamState.FINALIZADO,
      modulo: '060 - OPERACIONAL RACES',
      titulo: 'Exámenes Operacionales FAA',
    };

    render(<ExamCard exam={examData} />);

    expect(screen.getByText('FINALIZADO')).toBeInTheDocument();
  });
});

describe('ExamState enum values (RN-EST)', () => {
  it('verifica valores exactos del enum para mapeo de colores', () => {
    expect(ExamState.NO_PRESENTADO).toBe(0);
    expect(ExamState.INICIADO).toBe(1);
    expect(ExamState.COMPROBADO).toBe(2);
    expect(ExamState.FINALIZADO).toBe(3);
  });  
});
