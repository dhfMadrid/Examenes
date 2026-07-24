// Mock data para tests de exam-selection
import { ExamState } from '../../../shared/domain/scoringRules';

export interface ExamSelectionProps {
  examenes: Array<{
    id: string;
    estado: ExamState;
    modulo: string;
    titulo: string;
    preguntas?: number;
    tiempoDisponibilita?: number;
    fechaExamen: string;
  }>;
}

export const mockExamenes = [
  {
    id: 'exam-001',
    estado: ExamState.NO_PRESENTADO, // NP
    modulo: '010 - AIR LAW',
    titulo: 'Examen de Ley Aérea (Módulo 010)',
    preguntas: 80,
    tiempoDisponibilidad: 90,
    fechaExamen: '2026-07-15T09:00:00Z',
  },
  {
    id: 'exam-002',
    estado: ExamState.INICIADO, // INI
    modulo: '030 - PERFLIGHT',
    titulo: 'Examen de Perflight (Módulo 030)',
    preguntas: 45,
    tiempoDisponibilidad: 60,
    fechaExamen: '2026-07-16T10:00:00Z',
  },
];

export const mockExamenesCompleto = [
  ...mockExamenes,
  {
    id: 'exam-003',
    estado: ExamState.COMPROBADO, // COMP
    modulo: '050 - RACES',
    titulo: 'Examen de RACES (Módulo 050)',
    preguntas: 90,
    tiempoDisponibilidad: 120,
    fechaExamen: '2026-07-14T08:30:00Z',
  },
];

export const ExamStateLabels = {
  [ExamState.NO_PRESENTADO]: 'No Presentado',
  [ExamState.INICIADO]: 'Iniciado', 
  [ExamState.COMPROBADO]: 'Comprobado',
  [ExamState.FINALIZADO]: 'Finalizado',
};

export default mockExamenes;
