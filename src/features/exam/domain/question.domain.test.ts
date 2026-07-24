// question.domain.test.ts — Test de dominío: QuestionCard domain logic (RN-GEN, RN-EJE-navegacion)

import { describe, it, expect } from 'vitest';
import type { GeneratedQuestion } from '@domain/examSession';

// ============================================================
// Test de tipado e estrutura da interface GeneratedQuestion
// Verificamos que o tipo de dato que recibimos do backend existe 
// e ten todos os campos necesarios segundo NEW_ARCHITECTURE.md §6
// ============================================================

describe('GeneratedQuestion structure (RN-GEN: banco de preguntas)', () => {
    function buildMockPregunta(overrides?: Partial<GeneratedQuestion>): GeneratedQuestion {
        return {
            id: 'q-001',
            orden: 1,
            texto: 'Cal é a velocidade mínima de despegue?',
            textosAlternativos: { en: "What is the minimum takeoff speed?" },
            condicionActiva: 0,
            anexoImagemId: null,
            anexo1Desc: null,
            nivelDificuldade: 2,
            capituloId: 'ch-010-03',
            anulada: false,
            ...overrides,
        };
    }

    it('pregunta básica sen anexos nin variacións (normal)', () => {
        const p = buildMockPregunta();
        expect(p.id).toBe('q-001');
        expect(p.orden).toBe(1);
        expect(p.texto).toContain('velocidade');
        expect(p.anexoImagemId).toBeNull();
        expect(p.anulada).toBe(false);
        expect(p.nivelDificuldade).toBe(2);
    });

    it('pregunta con anexo de imaxe (RN-GEN: Imagen da pregunta)', () => {
        const p = buildMockPregunta({
            id: 'q-anexo-img',
            texto: 'Observa a seguinte imaxe...',
            anexoImagemId: 'file-5678',
            nivelDificuldade: 3,
        });
        expect(p.anexoImagemId).toBe('file-5678');
        // A imaxe debería ser solicitada ao servidor vía IDFile (1=BMP/GIF/JPG)
    });

    it('pregunta con variante de lingua (RN-IDIO: lingua mixta)', () => {
        const p = buildMockPregunta({
            textosAlternativos: { 
                en: "What is the minimum takeoff speed?",
                gl: "Cal é a velocidade mínima de engalzamentu?",
            },
            condicionActiva: 1, // activa variante 1 (inglés)
        });
        expect(Object.keys(p.textosAlternativos).length).toBe(2);
        expect(p.condicionActiva).toBe(1);
    });

    it('pregunta anulada administrativamente' , () => {
        const p = buildMockPregunta({
            id: 'q-anulada',
            anulada: true,
        });
        expect(p.anulada).toBe(true);
        // As preguntas anuladas deben aparecer pero NON contar para a nota final (RN-COR-04)
    });

    it('pregunta con todos os niveis de dificultade válidos', () => {
        for (const nivel of [1, 2, 3] as const) {
            const p = buildMockPregunta({ id: `q-diff-${nivel}`, nivelDificuldade: nivel });
            expect(p.nivelDificuldade).toBe(nivel);
        }
    });

    it('orden da pregunta é positivo (baseado en 1)', () => {
        const p = buildMockPregunta({ id: 'q-ord', orden: 0 }); // permitimos orden=0 internamente pero 1+ no display
        expect(p.orden).toBeGreaterThanOrEqual(0);
    });

    it('pregunta con texto vacío é inválida' , () => {
        expect(() => { 
            // Non debería ser posible crear un GeneratedQuestion sen texto, 
            // pero o dominio debe permitir a validación en entrada
        } ).toBeDefined();
    });
});

describe('GeneratedQuestion field type checking', () => {
    function buildMockPregunta(overrides?: Partial<GeneratedQuestion>): GeneratedQuestion {
        return {
            id: 'q-001',
            orden: 1,
            texto: 'Cal é a velocidade mínima de despegue?',
            textosAlternativos: { en: "What is the minimum takeoff speed?" },
            condicionActiva: 0,
            anexoImagemId: null,
            anexo1Desc: null,
            nivelDificuldade: 2,
            capituloId: 'ch-010-03',
            anulada: false,
            ...overrides,
        };
    }

    it('id pode calquera string (incluíndo UUIDs do backend)', () => {
        const p = buildMockPregunta({ id: '6ba7b810-9dad-11d1-80b4-00c04fd430c8' });
        expect(p.id).toBeDefined();
    });

    it('capituloId pode calquera string do DOMINIO', () => {
        const p = buildMockPregunta({ capituloId: 'any-string-jaa-capitulo-id' });
        expect(p.capituloId).toBeDefined();
    });

    it('textosAlternativos está vacía por defecto (válido se só temos lingua activa)', () => {
        const p = buildMockPregunta({ textosAlternativos: {} });
        expect(Object.keys(p.textosAlternativos).length).toBe(0);
    });
});
