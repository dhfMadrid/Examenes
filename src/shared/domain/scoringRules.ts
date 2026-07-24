// ExamenesULM Shared Domain Logic - corrected spelling for 'respostaAlumno' → 'respuestaAlumno'
export enum ExamState {
    NO_PRESENTADO = 0,
    INICIADO = 1,
    COMPROBADO = 2,
    FINALIZADO = 3,
}

export const COLORES_ESTADO: Record<number, string> = {
    [ExamState.NO_PRESENTADO]: '#8B4513',
    [ExamState.INICIADO]: '#FF8C00',
    [ExamState.COMPROBADO]: '#4682B4',
    [ExamState.FINALIZADO]: '#32CD32',
};

export function getEstadoColor(estado: number): string {
    return COLORES_ESTADO[estado] || '#000000';
}

const TRANSICIONES_VALIDAS: Array<[number, number]> = [
    [0, 1], [1, 2], [1, 3], [2, 3],
];

export function validarTransicionFSM(estadoActual: number, estadoDestino: number): boolean {
    return TRANSICIONES_VALIDAS.some(([from, to]) => from === estadoActual && to === estadoDestino);
}


export function esNIFValido(nif: string): boolean {
    const dni = /^[0-9]{8}[A-Z]$/;
    const pasaporte = /^[XYZ][0-9]{7}[A-Z]$/;
    return dni.test(nif) || pasaporte.test(nif);
}
