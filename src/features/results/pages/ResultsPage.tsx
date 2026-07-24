// ResultsPage.tsx — Pantalla de resultados post-examen (RN-COR, RN-EJE-04)
// Estilos adaptados a los mismos que LoginPage (LoginPage.css)

import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../auth-flow/context/AuthProvider';
import './ResultsPage.css';

interface ResultData {
    id?: number;
    examen_id?: string | number;
    correctas: number;
    fallos: number;
    noContestadas: number;
    porcentajeAcierto: number;
    esApto: boolean;
    notaFinal: number | null;
    mensajeResultado?: string;
    fechaCalculo?: string;
    tiempoRestanteSegundos?: number | null;
    tiempoTotalSegundos?: number | null;
    respuestasJson?: string | null;
    alumnoId?: number | null;
}

/** Fetch resultados finales desde el backend */
async function fetchResultado(examenId: string): Promise<ResultData | null> {
    try {
        const resp = await fetch(`/api/v1/resultados/${examenId}`);
        if (!resp.ok) return null;
        const data = await resp.json();
        // Mapear camelCase para el backend al formato que usa ResultsPage
        return {
            id: data.id ?? 0,
            examen_id: data.examen_id ?? examenId,
            correctas: data.correctas ?? 0,
            fallos: data.fallos ?? 0,
            noContestadas: data.no_contestadas ?? 0,
            porcentajeAcierto: data.porcentaje_acierto ?? 0,
            esApto: data.es_apto ?? false,
            notaFinal: data.nota_final ?? null,
            mensajeResultado: data.mensaje_resultado ?? '',
            fechaCalculo: data.fecha_calculo ?? '',
            tiempoRestanteSegundos: data.tiempo_restante_segundos ?? 0,
            tiempoTotalSegundos: data.tiempo_total_segundos ?? 0,
            respuestasJson: data.respuestas_json ?? null,
            alumnoId: data.alumno_id ?? null,
        };
    } catch {
        return null;
    }
}

interface Props {
    examId?: string | null;
}

export default function ResultsPage({ examId }: Props) {
    const { cerrarSesion, usuario } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    // Prioridad de examId: prop > state > null
    const resolvedExamId = (examId as string) ?? (location.state?.examId as string) ?? 'demo';

    const [loading, setLoading] = useState(true);
    const [resultados, setResultados] = useState<ResultData | null>(null);

    // Cargar resultados reales del backend
    useEffect(() => {
        let cancelled = false;
        (async () => {
            setLoading(true);
            const data = await fetchResultado(resolvedExamId);
            if (!cancelled && data) {
                setResultados(data);
            } else if (!cancelled && !data) {
                setResultados(null);
            }
            setLoading(false);
        })();
        return () => { cancelled = true; };
    }, [resolvedExamId]);

    // Nunca mostrar datos demo inventados — si no hay resultado real, se muestra "pendiente"

    if (loading) {
        return (
            <div className="results-page">
                <div className="loading-screen">
                    <div className="spinner" />
                    <div className="loading-text">Cargando resultados...</div>
                </div>
            </div>
        );
    }

    // Solo accedemos a resultados aquí, después del check de loading + null guard
    if (!resultados) {
        return (
            <div className="results-page">
                <div className="results-card">
                    <header className="results-card-header">
                        <h1>Resultado del Examen</h1>
                    </header>
                    <div className="results-card-body">
                        <p style={{ marginTop: 32, textAlign: 'center', color: '#64748b', fontSize: 16 }}>
                            Resultados no disponibles. Inténtalo de nuevo más tarde.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    const data = resultados; // safe after null guard above
    const porcentaje = Math.round(data.correctas / Math.max(1, data.correctas + data.fallos + data.noContestadas) * 100);
    const aprobado = data.esApto;

    return (
        <div className="results-page">
            <div className="results-card">
                {/* Header with gradient hero */}
                <header className="results-card-header">
                    <h1>Resultado del Examen</h1>
                    {usuario && (
                        <p className="results-user-info">
                            {usuario.nombre} {usuario.apellidos} — {usuario.nifPasaporte}
                        </p>
                    )}
                    <p className="exam-id-text">
                        Examen: {resolvedExamId}{resultados?.id ? ` (DB ID: ${resultados.id})` : ''}
                        {resultados?.fechaCalculo && ` | Fecha: ${new Date(resultados.fechaCalculo).toLocaleString('es-ES')}`}
                    </p>
                </header>

                {/* Body con score card */}
                <div className="results-card-body">
                    <div
                        className={`score-card ${aprobado ? 'aprobado' : 'suspendido'}`}
                        data-testid="score-card"
                    >
                        <h2>Puntuación Final</h2>

                        <div className="score-stats">
                            <ScoreItem label="ACIERTOS" value={data.correctas} colorClass="acierto" />
                            <ScoreItem label="FALLOS" value={data.fallos} colorClass="fallo" />
                            <ScoreItem label="NO CONTESTADAS" value={data.noContestadas} colorClass="noc" />
                        </div>

                        {/* Nota box */}
                        {data.notaFinal !== null && data.notaFinal !== undefined ? (
                            <div className="nota-box">
                                <span className="nota-label">Nota:</span>
                                <span className={`nota-valor ${aprobado ? 'aprobado' : 'suspendido'}`}>
                                    {data.notaFinal.toFixed(2)}
                                </span>
                            </div>
                        ) : null}

                        {/* Porcentaje + badge */}
                        <div className="porcentaje-box">
                            <span className="porcentaje-valor">{porcentaje}%</span>
                            <div>
                                <span className={`resultado-badge ${aprobado ? 'aprobado' : 'suspendido'}`}>
                                    {aprobado ? 'APROBADO' : 'SUSPENDIDO'}
                                </span>
                            </div>
                        </div>

                        {/* Info umbral */}
                        <p className="info-text">
                            Umbral de acierto (RN-COR-01): 75% → Necesitaba {Math.floor(50 * 75 / 100)} correctas mínimo. Obtuvo {data.correctas} correctas, {data.fallos} fallos, {data.noContestadas} sin respuesta.
                        </p>

                        {/* Mensaje extra del backend */}
                        {resultados.mensajeResultado && (
                            <p className="mensaje-resultado">
                                {resultados.mensajeResultado}
                            </p>
                        )}
                    </div>



                    {/* Actions row */}
                    <div className="actions-row">
                        <button
                            onClick={() => navigate('/seleccion')}
                            className="btn-revision"
                        >
                            Volver al panel
                        </button>
                        <button
                            onClick={() => { cerrarSesion(); navigate('/'); }}
                            className="btn-revision"
                        >
                            Cerrar Sesión
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

/* ── Sub-componentes ── */

function ScoreItem({ label, value, colorClass }: { label: string; value: number; colorClass: string }) {
    return (
        <div className="stat-item">
            <div className={`stat-value ${colorClass}`}>{value}</div>
            <div className="stat-label">{label}</div>
        </div>
    );
}

