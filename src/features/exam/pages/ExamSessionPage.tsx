// ExamSessionPage.tsx - Pantalla principal del examen (carga preguntas reales de la BD)
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { useAuth } from '../../auth-flow/context/AuthProvider';
import { ExamState, COLORES_ESTADO } from '@domain/scoringRules';
import { useTimerCountdown } from '../../timer/domain/useTimerCountdown';
import { fetchPreguntasDeExamen } from '@features/exam-selection/services/exam.api';

import '../../../shared/styles/shared.css';

const STORAGE_KEY = 'exam_session_draft';
const IMPUGNACIONES_KEY = 'exam_impugnaciones';

const ESTADOS_TEXTO = ['NO PRESENTADO', 'INICIADO', 'COMPROBADO', 'FINALIZADO'];

/** Timer display inline — homoxéneo coa paleta da app (Inter, sans-serif; gradiente header). */
function TimerDisplay({ segundosRestantes, isUrgente }: { segundosRestantes: number; isUrgente: boolean }) {
    const seg = Math.max(0, Math.floor(segundosRestantes));
    const h = String(Math.floor(seg / 3600)).padStart(2, '0');
    const m = String(Math.floor((seg % 3600) / 60)).padStart(2, '0');
    const s = String(seg % 60).padStart(2, '0');

    return (
        <div style={{
            padding: '8px 18px',
            background: isUrgente
                ? 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)'
                : 'linear-gradient(135deg, rgba(255,255,255,.18) 0%, rgba(255,255,255,.06) 100%)',
            borderRadius: 10,
            fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            fontSize: 24,
            fontWeight: 700,
            color: isUrgente ? '#fff' : '#fff',
            letterSpacing: 1.6,
            textAlign: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,.15)',
        }}>
            {`${h}:${m}:${s}`}
        </div>
    );
}

/** Grid de navegacion de preguntas */
function QuestionGrid({ questions, answers, currentIdx, onSelect, impugnaciones }: {
    questions: { id: string; orden: number }[];
    answers: string[];
    currentIdx: number;
    onSelect: (i: number) => void;
    impugnaciones: Record<number, string>;
}) {
    const RESPUESTA_COLORES: Record<string, { bg: string; fg: string }> = {
        A: { bg: '#dbeafe', fg: '#1d4ed8' },
        B: { bg: '#dcfce7', fg: '#15803d' },
        C: { bg: '#fef9c3', fg: '#a16207' },
        D: { bg: '#fae8ff', fg: '#9333ea' },
    };

    return (
        <div data-testid="question-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(10, 1fr)', gap: 4 }}>
            {questions.map((q, i) => {
                const ans = answers[i];
                const current = i === currentIdx;
                const tieneImpugnacion = impugnaciones[i] && impugnaciones[i].trim().length > 0;
                const isRespuesta = ans && ans !== '-' && RESPUESTA_COLORES[ans];
                return (
                    <div key={q.id} data-testid={`q-btn-${i+1}`} onClick={() => onSelect(i)}
                        style={{ cursor: 'pointer', width: 36, height: 36, position: 'relative' }}>
                        <div style={{ display: 'flex', alignItems: 'center', width: '100%', height: '100%' }}>
                            <div style={{
                                flex: isRespuesta ? '0 0 calc(100% - 12px)' : '0 0 100%',
                                height: '100%',
                                backgroundColor: current ? '#f5e6cc' : (isRespuesta ? RESPUESTA_COLORES[ans].bg : ans && ans !== '-' ? '#c8e6fa' : '#fff'),
                                border: current ? '2px solid #004080' : '1px solid #ccc',
                                borderTopLeftRadius: 3,
                                borderBottomLeftRadius: 3,
                                fontSize: 9,
                                fontWeight: 600,
                                color: '#1e293b',
                                fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                            }}>
                                {String(i+1).padStart(2,'0')}
                                {tieneImpugnacion && (
                                    <span style={{ color: '#e74c3c', fontWeight: 'bold' }}>&#9888;</span>
                                )}
                            </div>
                            {isRespuesta && (
                                <span style={{
                                    width: 12, height: 36,
                                    backgroundColor: RESPUESTA_COLORES[ans].bg,
                                    borderTopRightRadius: 3, borderBottomRightRadius: 3,
                                    borderLeft: '1px solid #e2e8f0',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: 8, fontWeight: 700, color: RESPUESTA_COLORES[ans].fg,
                                    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
                                }}>{ans}</span>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

/** Panel de impugnación inline */
function ImpugnacionPanel({ currentIdx, impugnaciones, onClose }: {
    currentIdx: number;
    impugnaciones: Record<number, string>;
    onClose: (texto: string) => void;
}) {
    const [texto, setTexto] = useState(impugnaciones[currentIdx] ?? '');
    const yaImpugnada = !!(impugnaciones[currentIdx]?.trim().length > 0);

    useEffect(() => {
        setTexto(impugnaciones[currentIdx] ?? '');
    }, [currentIdx]);

    return (
        <div data-testid="impugnacion-panel" style={{ marginTop: 16, padding: 12, background: '#fff3e0', border: '1px solid #ff9800', borderRadius: 6 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <h4 style={{ margin: 0, fontSize: 14, color: '#e65100' }}>
                    {yaImpugnada ? '⚠ Pregunta impugnada — Modificar impugnación' : 'Impugnar pregunta'}
                </h4>
                <button onClick={() => onClose(texto.trim())} data-testid="btn-close-impugnacion"
                    style={{ background: 'none', border: '1px solid #ccc', borderRadius: 3, padding: '2px 8px', cursor: 'pointer', fontSize: 12 }}>×</button>
            </div>
            <textarea data-testid="impugnacion-texto" value={texto} onChange={(e) => setTexto(e.target.value)}
                placeholder={yaImpugnada ? (impugnaciones[currentIdx] ?? '') : 'Razones de la impugnación...'}
                rows={3} style={{ width: '97%', padding: 8, border: '1px solid #ccc', borderRadius: 4, fontSize: 13, fontFamily: 'Arial, sans-serif', resize: 'vertical' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
                <span data-testid="impugnacion-char-count" style={{ fontSize: 11, color: '#888' }}>{texto.length} caracteres</span>
                <button onClick={() => onClose(texto.trim())} data-testid="btn-guardar-impugnacion"
                    style={{ padding: '6px 16px', background: yaImpugnada ? '#d32f2f' : '#da9921', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 13, fontWeight: 'bold' }}>
                    {yaImpugnada && texto.trim().length === 0 ? '✖ Eliminar impugnación' : '✔ Guardar impugnación'}
                </button>
            </div>
        </div>
    );
}

// ─── Tipos internos ──────────────────────────────────────────────
interface InternaQuestion {
    id: string; orden: number; texto: string; opciones: readonly ['A', 'B', 'C', 'D']; opcionesTexto: [string, string, string, string]; anexo: string | null; imagenUrl: string | null; respCorrecta?: string[];
}

export default function ExamSessionPage(_props: {}) {
    const auth = useAuth();
    const usuario = auth.usuario;
    const token = auth.token;
    const navigate = useNavigate();
    const params = useParams<{ examId: string }>();
    const navState = (useLocation().state as { nTest?: number; tTestSegundos?: number } | null);
    const examId = params.examId ?? 'demo-exam';

    // Timer countdown — la duración viene de navigate state como SEGUNDOS (tTestSegundos)
    const [duration, setDuration] = useState(5400); // default 90 min en segundos
    useEffect(() => {
        if (navState?.tTestSegundos && navState.tTestSegundos > 0) {
            setDuration(navState.tTestSegundos);
        } else if (navState?.nTest) {
            // estimar: 4min/pregunta (240s) como fallback
            setDuration(navState.nTest * 240);
        }
    }, [navState]);

    // useTimerCountdown recibe TIEMPO EN MINUTOS — convertimos de segundos a minutos
    const { remainingSeconds, isUrgent } = useTimerCountdown(Math.max(1, Math.floor(duration / 60)));

    // ── Estado de carga de preguntas reales ──
    const [questions, setQuestions] = useState<InternaQuestion[]>([]);
    const [loadingQ, setLoadingQ] = useState(true);
    const [errorQ, setErrorQ] = useState<string | null>(null);
    const [examConfig, setExamConfig] = React.useState({ nTest: 0, tTestSegundos: 5400 });

    // Cargar preguntas reales al montar el componente
    useEffect(() => {
        let cancelled = false;

        async function loadQuestions() {
            try {
                setLoadingQ(true);
                setErrorQ(null);
                const backendPreguntas = await fetchPreguntasDeExamen(examId);
                if (cancelled) return;

                // Adaptar al formato interno — opciones_texto vienen de la BD
                const adaptadas: InternaQuestion[] = backendPreguntas.map(bp => ({
                    id: `q-b${bp.id_banco}`,
                    orden: bp.orden_en_examen,
                    texto: bp.texto_enunciado,
                    opciones: ['A', 'B', 'C', 'D'] as const,
                    opcionesTexto: [
                        bp.opciones_a ?? '',
                        bp.opciones_b ?? '',
                        bp.opciones_c ?? '',
                        bp.opciones_d ?? '',
                    ],
                    anexo: null,
                    imagenUrl: bp.url_fichero ? String(bp.url_fichero).trim() : null,
                    respCorrecta: bp.respuesta_correcta,
                }));

                setQuestions(adaptadas);
                setExamConfig(prev => ({ ...prev, nTest: adaptadas.length }));
            } catch (e) {
                if (cancelled) return;
                setErrorQ(e instanceof Error ? e.message : 'Error al cargar preguntas');
                console.error('[ExamSession] Error cargando preguntas:', e);
            } finally {
                if (!cancelled) setLoadingQ(false);
            }
        }

        loadQuestions();
        return () => { cancelled = true; };
    }, [examId]);

    // Impugnaciones
    const [impugnaciones, setImpugnaciones] = useState<Record<number, string>>({});
    const [showImpugnacion, setShowImpugnacion] = useState(false);
    const [mostrarCalculadora, setMostrarCalculadora] = useState(false);
    const [showSuccess, setShowSuccess] = useState(false);

    // Draft guardado (para persistir respuestas entre navigations)
    const loadDraft = (eid: string) => {
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            const drafts: Record<string, any> = JSON.parse(raw);
            return drafts[eid] ?? null;
        } catch {/* ignore */}
        return null;
    };

    const loadImpugnaciones = (): Record<number, string> => {
        try {
            const raw = sessionStorage.getItem(IMPUGNACIONES_KEY);
            if (!raw) return {};
            const map: Record<number, string> = JSON.parse(raw);
            return map;
        } catch {/* ignore */}
        return {};
    };

    const saveImpugnaciones = (map: Record<number, string>) => {
        try { sessionStorage.setItem(IMPUGNACIONES_KEY, JSON.stringify(map)); } catch {/* ignore */}
    };

    const initialDraft = loadDraft(examId);
    const [estado] = useState(ExamState.INICIADO);
    const [currentQIdx, setCurrentQIdx] = React.useState(initialDraft?.currentQIdx ?? 0);
    const [answers, setAnswers] = React.useState<string[]>(initialDraft?.answers ?? Array(examConfig.nTest).fill('-'));

    // Session ID fijo — usar el del examen real (params.examId), no uno aleatorio.
    const sessionID = examId;

    // Guardar draft cuando cambian responses/posición
    useEffect(() => {
        if (questions.length === 0) return; // no guardar durante carga
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            const drafts: Record<string, any> = raw ? JSON.parse(raw) : {};
            drafts[examId] = { answers, currentQIdx };
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(drafts));
        } catch {/* ignore */}
    }, [answers, currentQIdx, examId, questions.length]);

    // Cargar impugnaciones previas solo al montar
    useEffect(() => {
        const saved = loadImpugnaciones();
        if (Object.keys(saved).length > 0) setImpugnaciones(saved);
    }, []);

    const handleImpugnacion = (texto: string) => {
        setImpugnaciones(prev => {
            const updated = { ...prev };
            if (texto.trim().length > 0) {
                updated[currentQIdx] = texto.trim();
            } else {
                delete updated[currentQIdx];
            }
            saveImpugnaciones(updated);
            return updated;
        });
        // Mostrar mensaje de éxito temporal (3 segundos)
        setShowSuccess(true);
        setTimeout(() => setShowSuccess(false), 3000);
        setShowImpugnacion(true); // mantener panel abierto
    };

    const marcar = (r: string) => { setAnswers(a => { const n = [...a]; n[currentQIdx] = r; return n; }); };

    // Construir el payload y enviar al backend antes de navegar a /resultados
    const submitir = async () => {
        console.log('[Finalizar] >>> INICIO — usuario:', !!usuario, 'examId:', examId, 'questions:', questions.length);
        try {
            console.log('[Finalizar] ✅ Fase 1: construyendo respuestas...');
            // Asegurar que NUNCA se envíen undefined → siempre incluir clave "respuesta"
            const respuestasPreguntas = questions.map((q, i) => ({
                numero: q.orden,
                respuesta: (answers[i] != null && answers[i] !== '-') ? answers[i] : '',
                impugnacion: impugnaciones[i]?.trim() || null,
            }));

            const body = {
                examId,
                sessionID,
                nifPasaporte: usuario?.nifPasaporte ?? '',
                respuestas: respuestasPreguntas,
                tiempoRestante: remainingSeconds,
                totalTiempo: examConfig.tTestSegundos,
            };

            console.log('[Finalizar] ✅ Fase 2: body construido:', JSON.stringify(body, null, 2));
            console.log('[Finalizar] ✅ Fase 3: JWT antes-fetch:', !!token);

            console.log('[Finalizar] >>> HACIENDO FETCH a /api/v1/examenes/finalizar ...'); // 🔍 TRAZA CRÍTICA
            const response = await fetch('/api/v1/examenes/finalizar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                },
                body: JSON.stringify(body),
            });
            console.log('[Finalizar] ✅ FETCH completado:', response.status, response.statusText);

            if (response.ok) {
                const data = await response.json();
                console.log('[Finalizar] ✅ Examen finalizado:', data);
                // Usar el examId integer que devuelve el backend, no el session_id string
                const dbExamId = data.examId;
                console.log('[Finalizar] >>> NAVIGATE a /resultados con examId (DB)=', dbExamId);
                navigate('/resultados', { state: { examId: String(dbExamId) } });
            } else {
                const errData = await response.json().catch(() => null);
                console.error('[Finalizar] ❌ Error HTTP:', response.status, errData);
                // Aun así navegar al resultado (siempre hay estado parcial)
                navigate('/resultados', { state: { examId } });
            }
        } catch (err) {
            console.error('[Finalizar] ❌ Exception al enviar examen:', err);
            // Si falla el fetch todavía navegamos — puede haber resultado pending
            navigate('/resultados', { state: { examId } });
        }
    };

    // ── Mostrar/ocultar automáticamente el panel de impugnación al cambiar de pregunta ──
    useEffect(() => {
        if (impugnaciones[currentQIdx] && impugnaciones[currentQIdx].trim().length > 0) {
            setShowImpugnacion(true);
        } else {
            setShowImpugnacion(false);
        }
    }, [currentQIdx]);

    const irAnterior = () => setCurrentQIdx((prev: number) => Math.max(0, prev - 1));
    const irSiguiente = () => setCurrentQIdx((cur: number) => Math.min(questions.length > 0 ? questions.length - 1 : 0, cur + 1));

    const showBtn = (show: boolean, el: React.ReactNode) => show ? el : null;

    // ── Render: estados de carga ──
    if (!usuario) return <div>No autenticado</div>;
    if (loadingQ) {
        return (
            <div data-testid="exam-session-page" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <div style={{ textAlign: 'center', color: '#64748b' }}>Cargando examen...</div>
            </div>
        );
    }
    if (errorQ) {
        return (
            <div data-testid="exam-session-page" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <div style={{ textAlign: 'center', color: '#ef4444' }}>Error cargando preguntas: {errorQ}</div>
            </div>
        );
    }
    if (questions.length === 0) {
        return (
            <div data-testid="exam-session-page" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <div style={{ textAlign: 'center', color: '#64748b' }}>No hay preguntas en este examen.</div>
            </div>
        );
    }

    const cur = questions[currentQIdx];
    const curAns = answers[currentQIdx] ?? '-';

    return (
        <div data-testid="exam-session-page" style={{ display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" }}>
            {/* Header */}
            <header data-testid="exam-header" style={{ display:'flex', justifyContent:'space-between', alignItems:'center', background:'linear-gradient(135deg, #1e40af 0%, #2563eb 60%, #7c3aed 100%)', padding:'12px 24px' }}>
                <div style={{background:'rgba(255,255,255,.1)', borderRadius:8, padding:'6px 16px', backdropFilter:'blur(4px)'}}>
                    <strong style={{color:'#fff', fontSize:15}}>{usuario?.licenciaDesc ?? 'Aula Virtual'}</strong>
                    {' | '}
                    <span style={{color:'rgba(255,255,255,.78)', fontSize:13}}>Session: {sessionID}  Estado: </span>
                    <span className="status-pill" style={{ background: `${COLORES_ESTADO[estado]}20`, color: COLORES_ESTADO[estado], borderColor: COLORES_ESTADO[estado] }}>{ESTADOS_TEXTO[estado]}</span>
                </div>
                <div style={{ display:'flex', flexDirection:'column', alignItems:'center' }}>
                    <span style={{ color:'rgba(255,255,255,.7)', fontSize:10, textTransform:'uppercase', letterSpacing:1 }}>Tiempo restante</span>
                    <div style={{}}>
                        <TimerDisplay segundosRestantes={remainingSeconds} isUrgente={isUrgent} />
                    </div>
                </div>
            </header>

            <div style={{ display:'flex', flex:1, overflow:'hidden' }}>
                {/* Main */}
                <main style={{ flex:1, padding:'24px 32px', overflowY:'auto', background:'#f8fafc' }}>
                    <p data-testid="q-counter" style={{fontSize:13,color:'#64748b'}}>
                        <b>Restante:</b> {Math.floor(remainingSeconds/3600)}h{String(Math.floor((remainingSeconds%3600)/60)).padStart(2,'0')}m<br/>
                        <b>NIF:</b> {(usuario?.nifPasaporte ?? 'N/A')}
                    </p>

                    <div data-testid="q-number" style={{marginBottom:4, fontSize:15, fontWeight:600, color:'#2563eb'}}>PREGUNTA: {String(cur.orden).padStart(2,'0')} de <span style={{fontWeight:700}}>{questions.length}</span></div>
                    <h3 data-testid="q-texto" style={{color:'#1e293b',fontSize:17, marginBottom:20, fontWeight:600}}>{cur.texto || 'Pregunta sin contenido'}</h3>

                    




                    <div data-testid="opciones-container" style={{display:'flex', flexDirection:'column', gap: 8}}>
                    <div data-testid="answer-options" style={{marginBottom:24}}>
                        {cur.opciones.map((letra, i) => {
                            const sel = curAns === letra;
                            return (
                                <label key={letra} onClick={() => marcar(letra)} data-testid={`option-${letra}`}
                                    style={{display:'flex',alignItems:'center',padding:'12px 18px',marginBottom:8,cursor:'pointer',border:sel?'2px solid #2563eb':'1.5px solid #e2e8f0',
                                            background:sel?'#eff6ff':'#fff',borderRadius:8,transition:'border-color .2s ease, box-shadow .2s ease',boxShadow: sel ? '0 0 0 3px rgba(37,99,235,.15)' : 'none'}}>
                                    <input type="radio" name="ans" checked={sel} readOnly onChange={()=>marcar(letra)} style={{marginRight:14}}/>
                                    <span style={{fontSize:14, color:'#1e293b'}}><span style={{fontWeight:600,color:'#2563eb'}}>{letra})</span> {cur.opcionesTexto[i] || `Opción ${letra}`}</span>
                                </label>
                            );
                        })}
                    </div>

                    {/* Anexo */}
                    {showBtn(!!(cur.anexo), (
                        <div data-testid="anexo-panel" style={{width: 360, padding: 14, background: '#f0fdf4', border: '1.5px solid #22c55e', borderRadius: 8, marginTop: 16}}>
                            <strong style={{fontSize:13,color:'#16a34a'}}>📎 Anexo visual</strong>
                        </div>
                    ))}

                    </div>

                    {/* Navegación */}
                    <div style={{display:'flex',gap:8,marginTop:24,alignItems:'center',flexWrap:'wrap'}}>
                        <button onClick={irAnterior} data-testid="btn-prev" disabled={currentQIdx === 0}
                            className="btn-secondary"
                            style={{padding:'9px 18px', background: currentQIdx === 0 ? '#f1f5f9' : 'transparent', border: currentQIdx === 0 ? '1.5px solid #e2e8f0' : '1.5px solid rgba(37,99,235,.35)', color: currentQIdx === 0 ? '#94a3b8' : '#2563eb', opacity: currentQIdx === 0 ? 0.5 : 1, cursor: currentQIdx === 0 ? 'not-allowed' : 'pointer', borderRadius:8, fontSize:14, fontWeight:500}}>← Anterior</button>
                        <button onClick={irSiguiente} data-testid="btn-next" disabled={currentQIdx === questions.length - 1}
                            className="btn-secondary"
                            style={{padding:'9px 18px', background: currentQIdx === questions.length - 1 ? '#f1f5f9' : 'transparent', border: currentQIdx === questions.length - 1 ? '1.5px solid #e2e8f0' : '1.5px solid rgba(37,99,235,.35)', color: currentQIdx === questions.length - 1 ? '#94a3b8' : '#2563eb', opacity: currentQIdx === questions.length - 1 ? 0.5 : 1, cursor: currentQIdx === questions.length - 1 ? 'not-allowed' : 'pointer', borderRadius:8, fontSize:14, fontWeight:500}}>Siguiente →</button>
                        <span style={{flex:1}}/>
                        <button onClick={() => setShowImpugnacion(p => !p)} data-testid="btn-impugnar"
                            className={showImpugnacion || impugnaciones[currentQIdx]?.trim() ? 'btn-primary' : 'btn-secondary'}
                            style={{padding:'9px 18px', background: (showImpugnacion || impugnaciones[currentQIdx]?.trim()) ? undefined : 'transparent', border: (showImpugnacion || impugnaciones[currentQIdx]?.trim()) ? 'none' : '1.5px solid rgba(37,99,235,.35)', color: (showImpugnacion || impugnaciones[currentQIdx]?.trim()) ? '#fff' : '#2563eb', borderRadius:8, cursor:'pointer', fontSize:14, fontWeight:(showImpugnacion || impugnaciones[currentQIdx]?.trim()) ? 600 : 500}}>
                            ⚠️ {impugnaciones[currentQIdx]?.trim() ? 'Modificar impugnación' : 'Impugnar pregunta'}
                        </button>
                        <button onClick={() => setMostrarCalculadora(p => !p)} data-testid="btn-calculadora"
                            className={mostrarCalculadora ? 'btn-primary' : 'btn-secondary'}
                            style={{padding:'9px 18px', background: mostrarCalculadora ? undefined : 'transparent', border: mostrarCalculadora ? 'none' : '1.5px solid rgba(37,99,235,.35)', color: mostrarCalculadora ? '#fff' : '#2563eb', borderRadius:8, cursor:'pointer', fontSize:14, fontWeight:500}}>🧮 Calculadora</button>
                    </div>

                    
                    {/* Respuestas bar */}
                    {questions.length > 0 && (
                        <div style={{marginTop:20, padding:'14px 16px', background:'#eff6ff', border:'1px solid rgba(37,99,235,.12)', borderRadius:8, fontSize:13}}>
                            {(() => {
                                const answered = answers.filter(a => a !== '-').length;
                                const pending = questions.length - answered;
                                return (
                                    <>
                                        <span style={{color:'#64748b'}}>Respondidas: <strong style={{color:'#1e293b'}}>{answered}/{questions.length}</strong></span><br/>
                                        {pending > 0 ? (
                                            <span style={{color:'#ef4444',fontWeight:600}}>Pendientes: {pending}</span>
                                        ) : (
                                            <span style={{color:'#22c55e',fontWeight:600}}>🎉 Todas respondidas</span>
                                        )}
                                    </>
                                );
                            })()}
                        </div>
                    )}



                    {/* Panel impugnación */}
                    {showBtn(showImpugnacion, (
                        <ImpugnacionPanel currentIdx={currentQIdx} impugnaciones={impugnaciones} onClose={handleImpugnacion} />
                    ))}

                    {/* Mensaje de éxito */}
                    {showSuccess && (
                        <div style={{ marginTop: 12, padding: '8px 14px', background: '#ecfdf5', border: '1px solid #6ee7b7', borderRadius: 6 }}>
                            <span style={{ color: '#15803d', fontSize: 13, fontWeight: 500 }}>✅ Impugnación guardada correctamente</span>
                        </div>
                    )}

                    {cur.imagenUrl && (
                        <div style={{marginBottom: 16, marginTop: 24, textAlign:'center'}}>
                            <img src={cur.imagenUrl} alt={`Imagen de la pregunta ${String(cur.orden).padStart(2,'0')}`} style={{maxWidth:'100%', maxHeight:300, objectFit:'contain', borderRadius:6, border:'1px solid #cbd5e1', padding: 8, background: '#fff', boxShadow: '0 1px 4px rgba(0,0,0,.08)'}} />
                        </div>
                    )}




                </main>

                {/* Sidebar */}
                <aside style={{width:480,padding:'0',background:'#fff',borderLeft:'1px solid #e2e8f0',display:'flex',flexDirection:'column'}}>
                    <div style={{padding:'16px 20px 12px', borderBottom:'1px solid #e2e8f0'}}>
                        <h4 data-testid="nav-panel" style={{color:'#1e293b',margin:0, fontSize:15, fontWeight:700}}>📋 NAVEGACIÓN PREGUNTAS</h4>
                    </div>
                    <div style={{padding:'12px 16px',overflowY:'auto',flex:1}}>
                        <QuestionGrid answers={answers} questions={questions} currentIdx={currentQIdx} onSelect={setCurrentQIdx} impugnaciones={impugnaciones}/>
                    </div>
                    {Object.keys(impugnaciones).length > 0 && (
                        <div style={{padding:'8px 16px', background:'#fff7ed', border:'1px solid rgba(255,152,0,.2)', borderTop:'1px solid #e2e8f0'}}>
                            <span style={{fontSize:12, color:'#e65100', fontWeight:500}}>⚠️ {Object.keys(impugnaciones).length} pregunta{Object.keys(impugnaciones).length > 1 ? 's' : ''} impugnada{Object.keys(impugnaciones).length > 1 ? 's' : ''}</span>
                        </div>
                    )}
                    <div style={{padding:'16px', borderTop:'1px solid #e2e8f0'}}>
                        {mostrarCalculadora && (
                            <div data-testid="calculadora-panel" style={{ display: mostrarCalculadora ? 'block' : 'none', marginBottom: 12, borderRadius: 8, overflow:'hidden', border:'1.5px solid #e2e8f0'}}>
                                <iframe src="https://www.desmos.com/scientific?lang=es" width="100%" height="280" frameBorder="0" allow="clipboard-write" title="Calculadora Desmos" style={{ display: 'block' }} />
                            </div>
                        )}
                        <button onClick={submitir} data-testid="btn-submit" className="btn-primary"
                            style={{width:'100%',display:'inline-flex',justifyContent:'center',alignItems:'center',padding:'13px 16px',fontSize:15,fontWeight:600,borderRadius:8}}>FINALIZAR EXAMEN</button>
                    </div>
                </aside>
            </div>

            <style>{`@media print { aside,.btn-exam{display:none!important;} } `}</style>
        </div>
    );
}
