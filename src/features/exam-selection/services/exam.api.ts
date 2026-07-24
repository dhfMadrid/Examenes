// exam.api.ts — Obtener exámenes del alumno desde la BD (SQL Server / FastAPI)
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8001/api/v1' : '/api/v1');

export interface BackendExam {
    sessionId: string;
    estado: number;  // 0=NP, 1=INI, 2=COMP, 3=FINALIZADO
    codModulo: string;
    moduloDescricao: string;
    titulo: string;
    nTest: number;
    tTestSegundos: number;
    fechaExamen: string | null;
    porcApto: number;
}

export function obtenerExamenesUrl(nifPasaporte: string): string {
    return `${API_BASE}/examenes?nif_pasaporte=${encodeURIComponent(nifPasaporte)}`;
}

export async function fetchExamenes(nifPasaporte: string): Promise<BackendExam[]> {
    const resp = await fetch(obtenerExamenesUrl(nifPasaporte));
    if (!resp.ok) {
        throw new Error(`Failed to load exams: ${resp.status} ${resp.statusText}`);
    }
    const json = await resp.json();
    return json.examenes || [];
}

// ── Interfaz de pregunta que devuelve el backend ──
export interface BackendPregunta {
    id_banco: number;       // PK en preguntas_banco
    orden_en_examen: number; // 1..N dentro del examen generado
    texto_enunciado: string;
    url_fichero: string | null;
    opciones_a: string | null;
    opciones_b: string | null;
    opciones_c: string | null;
    opciones_d: string | null;
    respuesta_correcta: string[]; // ["A"] o ["A","C"] etc.
}

// ── Generar y obtener las preguntas aleatorias de un examen ──
export function generarExamenesPreguntasUrl(examId: string): string {
    return `${API_BASE}/examenes/${encodeURIComponent(examId)}/generar`;
}

export async function fetchPreguntasDeExamen(examId: string): Promise<BackendPregunta[]> {
    // Primero: generar el examen (SELECT aleatorio + INSERT en examen_preguntas)
    const generarUrl = generarExamenesPreguntasUrl(examId);
    const respGenerar = await fetch(generarUrl, { method: 'POST' });
    if (!respGenerar.ok) {
        throw new Error(`Error al generar examen: ${respGenerar.status} ${respGenerar.statusText}`);
    }
    
    // Luego: obtener las preguntas generadas
    const respPreg = await fetch(obtenerExamenesPreguntasUrl(examId));
    if (!respPreg.ok) {
        throw new Error(`Error al cargar preguntas del examen: ${respPreg.status} ${respPreg.statusText}`);
    }
    const json = await respPreg.json();
    return json.preguntas || [];
}

export function obtenerExamenesPreguntasUrl(examId: string): string {
    return `${API_BASE}/examenes/${encodeURIComponent(examId)}/preguntas`;
}
