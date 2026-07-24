// ExamSelectionPage.tsx — Panel de selección de examen (US-02, RN-EST-01, RN-MAT)
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth-flow/context/AuthProvider';
import { ExamCard } from '../components/ExamCard';
import { fetchExamenes, type BackendExam } from '@features/exam-selection/services/exam.api';
import { ExamState } from '@domain/scoringRules';
import '@styles/shared.css';

/** Mapear BackendExam al formato interno que espera ExamCard */
function toInternalExam(be: BackendExam) {
    return {
        id: be.sessionId,
        estado: be.estado as number,
        modulo: `${be.codModulo} - ${be.moduloDescricao}`,
        titulo: be.titulo,
        preguntas: be.nTest,
        tiempoDisponibilidad: Math.round(be.tTestSegundos / 60),
        fechaExamen: be.fechaExamen ?? undefined,
    };
}

// ── Status pill para summary bar ──
function StatusPill({ count, label, color }: { 
    count: number; 
    label: string; 
    color: string 
}) {
    if (count === 0) return null;
    return (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '5px 12px', borderRadius: 999, background: `${color}18`, border: `1px solid ${color}30` }}>
            <span style={{ fontWeight: 700, fontSize: 13, color }}>●</span>
            <span style={{ fontWeight: 600, fontSize: 12.5, color }}>{count}</span>
            <span style={{ fontWeight: 500, fontSize: 12, color: '#475569', marginLeft: 4 }}>{label}</span>
        </div>
    );
}

export default function ExamSelectionPage() {
    const { usuario, cerrarSesion } = useAuth();
    const navigate = useNavigate();

    const [exams, setExams] = useState<BackendExam[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Cargar exámenes desde la BD vía API del backend (/api/v1/examenes?nif_pasaporte=...)
    useEffect(() => {
        let cancelled = false;

        async function load() {
            if (!usuario) return;
            try {
                const data = await fetchExamenes(usuario.nifPasaporte);
                if (!cancelled) setExams(data);
            } catch (e) {
                if (!cancelled) setError(e instanceof Error ? e.message : 'Error al cargar exámenes');
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        if (usuario) load();
        return () => { cancelled = true; };
    }, [usuario]);

    // Mapear datos internos para estado/count y renderizado
    const internalExams = useMemo(() => exams.map(toInternalExam), [exams]);
    const estadoCount = useMemo(() => {
        const s = internalExams.map(e => e.estado);
        return {
            NO_PRESENTADO: s.filter(v => v === ExamState.NO_PRESENTADO).length,
            INICIADO: s.includes(ExamState.INICIADO) ? 1 : 0,
            COMPROBADO: s.includes(ExamState.COMPROBADO) ? 1 : 0,
            FINALIZADO: s.filter(v => v === ExamState.FINALIZADO).length,
        };
    }, [internalExams]);

    if (!usuario) return <div>No autenticado</div>;

    // Loading state
    if (loading) {
        return (
            <div className="page-shell">
                <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>
                    Cargando exámenes...
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="page-shell">
                <div style={{ textAlign: 'center', padding: 40, color: '#ef4444' }}>
                    Error al cargar exámenes: {error}
                </div>
            </div>
        );
    }

    return (
        <div className="page-shell">
            <div style={{ width: '100%', maxWidth: 720 }}>
                {/* Header con gradiente */}
                <div className="page-header-bar">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative' }}>
                        <div>
                            <h1>🎓 Aula Virtual</h1>
                            <p>{usuario.nombre} {usuario.apellidos} — NIF: {usuario.nifPasaporte}</p>
                        </div>
                        <button
                            onClick={() => { cerrarSesion(); navigate('/login'); }}
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 5,
                                padding: '6px 10px',
                                fontSize: 13,
                                fontWeight: 500,
                                color: '#ffffff',
                                background: 'rgba(255,255,255,.1)',
                                border: '1px solid rgba(255,255,255,.2)',
                                borderRadius: 6,
                                cursor: 'pointer',
                                transition: 'background .15s ease',
                                fontFamily: "'Inter', sans-serif",
                            }}
                            onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,.2)"}
                            onMouseLeave={e => e.currentTarget.style.background = "rgba(255,255,255,.1)"}
                        >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                                <polyline points="16 17 21 12 16 7"/>
                                <line x1="21" y1="12" x2="9" y2="12"/>
                            </svg>
                            <span style={{ marginTop: 1 }}>cerrar sesión</span>
                        </button>
                    </div>
                </div>

                {/* Card body */}
                <div className="page-card-body">

                    {/* Summary bar de estados — white elevated card */}
                    <h2 style={{ fontSize: 18, color: '#ffffff', marginBottom: 12 }}>Número de exámenes disponibles por estado</h2>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', padding: '16px 18px', marginBottom: 20, borderRadius: 12, background: '#fff', boxShadow: '0 4px 10px rgba(0,0,0,.06)' }}>
                        <StatusPill count={estadoCount.NO_PRESENTADO} label="No presentado" color="#8B4513" />
                        <StatusPill count={estadoCount.INICIADO} label="Iniciado" color="#FF8C00" />
                        <StatusPill count={estadoCount.COMPROBADO} label="Comprobado" color="#4682B4" />
                        <StatusPill count={estadoCount.FINALIZADO} label="Finalizado" color="#22c55e" />
                    </div>

                   

                    {/* Lista de exámenes */}
                    <h2 style={{ fontSize: 18, color: '#ffffff', marginBottom: 12 }}>Exámenes disponibles</h2>
                    {internalExams.length === 0 ? (
                        <p style={{ color: '#64748b', fontStyle: 'italic' }}>No tienes exámenes asignados.</p>
                    ) : (
                        internalExams.map(exam => (
                            <ExamCard key={exam.id} exam={exam} onAction={(examId) => navigate(`/examen/${examId}`, { state: { nTest: exam.preguntas, tTestSegundos: exam.tiempoDisponibilidad * 60 } })} />
                        ))
                    )}

                    {/* Instrucciones */}
                    <details style={{ marginTop: 32, padding: '14px 18px', background: 'rgba(255,255,255,.06)', border: '1px solid rgba(255,255,255,.08)', borderRadius: 12 }}>
                        <summary style={{ fontSize: 14, fontWeight: 600, color: '#ffffff', marginBottom: 8, cursor: 'pointer' }}>📋 Instrucciones importantes</summary>
                        <ul style={{ marginTop: 4, fontSize: 13.5, lineHeight: 1.7, color: '#cbd5e1' }}>
                            <li>Su examen estará preparado el día matriculado y los días sucesivos.</li>
                            <li>El examen tendrá una duración limitada y se mostrará en todo momento.</li>
                            <li>Puede finalizar el examen en todo momento con el botón "Finalizar".</li>
                            <li>Puede impugnar una pregunta si observa algún error con el botón "Impugnar".</li>
                            <li>Puede mostrar y ocultar la calculadora si lo necesita con el botón "Calculadora".</li>
                        </ul>
                    </details>
                </div>
            </div>
        </div>
    );
}
