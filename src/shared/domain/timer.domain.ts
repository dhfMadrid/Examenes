// timer.domain.ts — Lóxica pura para o cronómetro do examen (RN-EJE-01, RN-EJE-02, RN-EJE-04)

/**
 * Formata segundos en formato HH:MM:SS separado por guións.
 * O sistema orixinal usa 'HH:MM:SS' no querystring para o auto-save.
 * @param totalSegundos — valor absoluto en segundos do countdown
 */
export function formatTimeFromSeconds(totalSegundos: number): string {
    const seg = Math.max(0, Math.floor(totalSegundos));
    const horas = Math.floor(seg / 3600);
    const mins = Math.floor((seg % 3600) / 60);
    const secs = seg % 60;
    return `${pad2(horas)}:${pad2(mins)}:${pad2(secs)}`;
}

/**
 * Formata segundos en formato HH:MM (para o display no UI do countdown).
 */
export function formatTimeDisplay(totalSegundos: number): string {
    const seg = Math.max(0, Math.floor(totalSegundos));
    const horas = Math.floor(seg / 3600);
    const mins = Math.floor((seg % 3600) / 60);
    return `${pad2(horas)}:${pad2(mins)}`;
}

/**
 * Calcula os segundos restantes do countdown.
 * @param totalSegundos - tempo total inicial en segundos (TTest * 60)
 * @param decorridoMs - milisegundos transcorridos desde o inicio
 */
export function calcularRestante(totalSegundos: number, decorridoMs: number): number {
    const restante = totalSegundos * 60 * 1000 - decorridoMs;
    return Math.max(0, Math.floor(restante / 1000));
}

/** Comprueba se o countdown expirou */
export function estaExpirado(totalMinutos: number, decorridoMs: number): boolean {
    return calcularRestante(totalMinutos, decorridoMs) <= 0;
}

/**
 * Regla RN-EJE-02: Para o Módulo 13 (item==32 + BBDD LMA), o exame divide en dúas partes.
 * Cada parte = TTest/2 minutos máis 30 segundos adicionais.
 */
export function dividirModulo13(tTestMinutos: number): {
    parte1TempoSeg: number;
    parte2TempoSeg: number;
} {
    const minPerParte = Math.floor(tTestMinutos / 2);
    return {
        parte1TempoSeg: minPerParte * 60 + 30,
        parte2TempoSeg: minPerParte * 60 + 30,
    };
}

// ======================== Regra RN-EJE-04: tempo de revisión post-submit ==============

/** Tempo fixo de revisión tras enviar o examen: 5 minutos (RN-EJE-04) */
export const REVISION_TIME_SECONDS = 300;

/** Comprobación se a cor do timer debe ser vermella (<60s) */
export function estaCercaDeExpirar(segundosRestantes: number): boolean {
    return segundosRestantes < 60 && segundosRestantes > 0;
}

// ======================== Helper =========

function pad2(n: number): string {
    return String(n).padStart(2, '0');
}

// ======================== Persistencia temporal real (sesión longa) ===========

export interface RestanteResultado {
    /** Segundos restantes do countdown */
    restanteSegundos: number;
    /** Se o tempo xa expirou */
    expirado: boolean;
}

/**
 * Calcula os segundos restantes basándose nun instante temporal real.
 * @param totalSegundos - duración total do exame en segundos (ex: 90*60=5400)
 * @param inicioInicioTimestamp - Date.now() momento ao que comeza o exame
 */
export function calcularRestanteReal(totalSegundos: number, inicioInicioTimestamp: number): RestanteResultado {
    const decorridoMs = Date.now() - inicioInicioTimestamp;
    const totalMs = totalSegundos * 1000;
    const restante = Math.max(0, Math.floor((totalMs - decorridoMs) / 1000));
    return {
        restanteSegundos: restante,
        expirado: restante <= 0,
    };
}
