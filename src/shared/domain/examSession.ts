// examSession.ts — Tipos e regras de dominio da sesión de exame

/**
 * Partes do exame (RN-INT): Test, Desenv 1, Desenv 2.
 * Os valores numéricos son os que usa o backend para controlar o estado.
 */
export enum ExamPart {
    TEST = 1,       // so test ou primeira parte
    DESARROLLO_1 = 2,// dev part I (ou segunda se NDesa=0)
    DESARROLLO_2 = 3,// dev part II (só NDesa=2)
}

/** Intervalo de tempo entre auto-guardados en milisegundos */
export const AUTO_SAVE_INTERVAL_MS = 60_000; // cada 60s (RN-EJE: guardado cada minuto)

/** Tempo de revisión post-submit: 5 minutos fixos (RN-EJE-04) */
export const REVISION_TIME_SECONDS = 300;

export interface Answer {
    /** Índice da pregunta no examen (0-based) */
    questionIndex: number;
    /** Resposta seleccionada: '-' = sen contestar, 'A'/'B'/'C'/'D' = resposta */
    response: string;
}

export interface GeneratedQuestion {
    /** ID interno da pregunta no banco */
    id: string;
    /** Posición dentro deste exame específico */
    orden: number;

    // --- Enunciado (con soporte de variantes condicionais por lingua) ---
    /** Texto principal do enunciado */
    texto: string;
    /** Variantes alternativas do enunciado (para lingua/nivel variábel) */
    textosAlternativos: Record<string, string>;
    /** Condición activa para o texto actual: que variante está activa */
    condicionActiva: number;

    // --- Imaxes/documentos anexos ---
    /** ID do arquivo anexo (se existe). Se null/undefined non ten anexo */
    anexoImagemId: string | null;
    /** Descrición do anexo complementario 1 (se aparece) */
    anexo1Desc: string | null;

    // --- Nivel de dificultade e capítulo ---
    nivelDificuldade: number; // 1=fácil, 2=medio, 3=difícil
    capituloId: string;

    /** Se esta pregunta foi anulada administrativamente (non conta na puntuación) */
    anulada: boolean;
}

/** Puntuación dunha pregunta individual para informes internos */
export interface QuestionScore {
    correcta: boolean;
    fallos: number;      // número de fallos nesta resposta específica (se HCo activo)
    noContestada: boolean;
    /** Se o alumno marcou discrepancia sobre esta pregunta */
    conDiscrepancia: boolean;
    // Texto da discrepancia se existe (orden~discrepancia separador ø~)
    textoDiscrepancia: string | null;
}

export interface GeneratedExam {
    sessionId: string;
    /** Estado actual: 0=NP, 1=INI, 2=COMP, 3=FIN */
    estado: number;
    /** Módulo (código) — ex. "010" AIR LAW */
    codModulo: string;
    /** Descrición do módulo: "Air Law" etc. */
    moduloDescricao: string;
    /** ID da matrícula/licencia do alumno */
    matriculaId: string;
    /** NIF/Pasaporte do alumno (para cabecera) */
    nifPasaporte: string;
    /** Nome completo para cabecera */
    nomeAlumno: string;
    /** Número total de preguntas do test */
    nTest: number;
    /** Tempo total en segundos (RN-EST: TTest) */
    tTestSegundos: number;
    /** Tempo restante por parte se Módulo 13 dividido */
    mod13Parte1Tempo?: number | null;
    mod13Parte2Tempo?: number | null;
    /** Se o módulo é especial (item==32 + BBDD LMA) → divide en dúas partes (RN-EJE-02) */
    esModulo13Dividido: boolean;
    /** Idioma do exame: 1=Inglés, 2=Espanol, 3=Mixto (RN-IDIO-01) */
    idiomaEspanol: number;
    /** Umbral de acerto para aprobar en % (tipico 75%) */
    porcAptoTest: number;
    /** Lista de preguntas xeradas */
    preguntasGeneradas: GeneratedQuestion[];
    /** O alumno está exento do test por HCo? */
    tieneHcoTestAprobado: boolean;
    /** Tempo en revisión post-submit (RN-EJE-04) */
    tiempoRevisionMaxSeg: number;
}

export interface AlumnoDatos {
    nifPasaporte: string;
    nombre: string;
    apellidos: string;
    codLicencia: string;
    licenseDescricao: string;

    // Campos de matrícula/licencia (RN-MAT)
    matriculaId: string;
    codModulo: string;
    moduloDescricao: string;
    nTest: number;
    tTest: number;          // minutos
    porcAptoTest: number;
    tieneHcoDesaAprobado: boolean;
}

