// LoginPage.tsx — Pagina completa de login + MFA flow (RN-AUT-01 a RN-AUT-05)
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { validarCredencialesLogin } from '../domain/auth.domain';
import { AuthServiceProd, guardarJWT } from '../domain/auth.api';
import { useAuth } from '../context/AuthProvider';
import { MFAScreen } from '../MFAScreen';
import './LoginPage.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';



interface LoginPageProps {}
// ── Barra de intensidad de contraseña (reutilizada del LoginForm) ──
function StrengthMeter({ password }: { password: string }) {
    const checks = [
        { id: "len", label: "8+ caracteres", ok: password.length >= 8 },
        { id: "mai", label: "Mayúscula", ok: /[A-Z]/.test(password) },
        { id: "min", label: "Minúscula", ok: /[a-z]/.test(password) },
        { id: "dig", label: "Dígito", ok: /[0-9]/.test(password) },
    ];

    const strength = checks.filter(c => c.ok).length;
    const barWidth = Math.max(6, (strength / 4) * 100);
    const barColor = strength <= 1 ? '#ef4444' : strength === 2 ? '#f59e0b' : strength === 3 ? '#3b82f6' : '#22c55e';

    return (
        <div style={{ marginBottom: 14 }}>
            <div className="strength-bar-wrap">
                <div className="strength-bar-fill" style={{ width: `${barWidth}%`, backgroundColor: barColor }} />
            </div>
            <ul className="strength-checklist">
                {checks.map(c => (
                    <li key={c.id} style={{ color: c.ok ? '#16a34a' : undefined }}>
                        {c.ok ? '✅ ' : '⬜ '}{c.label}
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default function LoginPage(_props: LoginPageProps) {
    const navigate = useNavigate();
    const auth = useAuth();


    type FlowStep = 'login' | 'mfa-challenge' | 'loading';
    const [flowStep, setFlowStep] = useState<FlowStep>('login');
    const [nifInput, setNifInput] = useState("");
    const [passwordInput, setPasswordInput] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);

    // --- Paso 1: login de credenciales (siempre llama al webservice) ---
    const handleLoginSubmit = async () => {
        // Limpiar estado previo
        setError(null);

        // Validar con dominio RN-AUT-01 + AUT-03
        const trimmedNif = nifInput.trim();
        const validation = validarCredencialesLogin(trimmedNif, passwordInput);
        if (!validation.valid) {
            setError(validation.error ?? 'Credenciales invalidas');
            return;
        }

        setLoading(true);
        setFlowStep('loading');

        try {
            // Backend: POST /api/v1/auth/login → tokenTemporal + requiereMFA
            const client = new AuthServiceProd(API_BASE);
            const response = await client.login({
                nifPasaporte: trimmedNif.toUpperCase(),
                password: passwordInput
            });

            if (!response.exitoso) {
                // Mensaje genico (RN-SEG-01: no revelar que campo fallo)
                setError('El intento de conexion no fue correcto. Intente de nuevo.');
                setFlowStep('login');
                return;
            }

            if (response.requiereMFA && response.tokenTemporal) {
                // Paso 2: mostrar MFA con el token temporal recibido
                setFlowStep('mfa-challenge');
            } else {
                // Sin MFA necesario → redirigir directo a seleccion
                navigate('/seleccion');
            }

        } catch {
            setError('Error de conexion con el servidor');
            setFlowStep('login');
        } finally {
            if (flowStep !== 'mfa-challenge') {
                setLoading(false);
            }
        }
    };

    // --- Paso 2: verificacion MFA exitosa ---
    const handleMfaSuccess = async (codigoIngresado: string) => {
        console.log('[LoginPage] handleMfaSuccess called, codigo=', JSON.stringify(codigoIngresado));
        setFlowStep('loading');
        setError(null);
        try {
            const client = new AuthServiceProd(API_BASE);
            const response = await client.verifyMFA({
                nifPasaporte: nifInput.trim().toUpperCase(),
                codigoMFA: codigoIngresado  // ← usa el código real del usuario
            });

            console.log('[LoginPage] MFA response raw:', JSON.stringify(response));
            if (response.exitoso && response.jwtToken) {
                console.log('[LoginPage] MFA exitoso, actualizando sesión sync...');
                const updated = auth.actualizarSesionSincronizada(nifInput.trim().toUpperCase(), response.jwtToken);
                console.log('[LoginPage] actualizarSesionSync result:', updated);
                
                if (updated) {
                    console.log('[LoginPage] MFA exitoso, navegando a /seleccion');
                    navigate('/seleccion');
                    console.log('[LoginPage] navigate() ejecutado');
                } else {
                    // fallback: guardar manual y navegar
                    guardarJWT(response.jwtToken);
                    window.dispatchEvent(new Event('jwt-stored'));
                    navigate('/seleccion');
                }
                return;
            } else {
                console.warn('[LoginPage] MFA NO exitoso:', JSON.stringify({ exitoso: response.exitoso, jwtToken: !!response.jwtToken }));
                setError('Codigo de verificacion incorrecto.');
                setFlowStep('mfa-challenge');
            }
        } catch (err) {
            console.error('[LoginPage] MFA exception:', err);
            setError('Error al verificar codigo MFA. Intente novamente.');
            setFlowStep('mfa-challenge');
        } finally {
            console.log('[LoginPage] handleMfaSuccess done, flowStep=', flowStep);
            setLoading(false);
        }
    };

    const handleMfaBack = () => {
        setFlowStep('login');
        setError(null);
    };

    // ── Renderizado condicional segun el paso del flujo ---

    /* ═══ Paso 2: MFA (wrapper igual al login) ═ */
    if (flowStep === 'mfa-challenge') {
        return (
            <div className="login-page">
                <div className="login-card">
                    <MFAScreen
                        nifPasaporte={nifInput}
                        onVerifySuccess={handleMfaSuccess}
                        onBack={handleMfaBack}
                        isLoading={loading}
                    />
                </div>
            </div>
        );
    }

    // ── Paso 1: formulario de login (diseño profesional) ---
    if (flowStep === 'login') {
        return (
            <div className="login-page">
                <div className="login-card">
                    {/* Header con gradiente */}
                    <div className="login-card-header">
                        <div className="login-logo">🎓</div>
                        <h2>Acceso a Aula Virtual</h2>
                        <p>Exámenes ULM — Plataforma de evaluación</p>
                    </div>

                    {/* Body con formulario */}
                    <div className="login-card-body">
                        {error && (
                            <div className="login-error" data-testid="login-error">
                                <span>⚠️</span>
                                <span>{error}</span>
                            </div>
                        )}

                        {/* Campo NIF/Pasaporte */}
                        <div className="form-group">
                            <label htmlFor="nif">NIF / Pasaporte</label>
                            <input
                                id="nif"
                                type="text"
                                value={nifInput}
                                onChange={e => { setNifInput(e.target.value); setError(null); }}
                                placeholder="DNI / NIF de alumno"
                                autoComplete="username"
                            />
                        </div>

                        {/* Campo Contraseña */}
                        <div className="form-group">
                            <label htmlFor="password">Contraseña</label>
                            <div className="form-input-wrap">
                                <input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    value={passwordInput}
                                    onChange={e => { setPasswordInput(e.target.value); setError(null); }}
                                    placeholder="Contraseña"
                                    autoComplete="current-password"
                                />
                                <button
                                    type="button"
                                    className="password-toggle-btn"
                                    onClick={() => setShowPassword(v => !v)}
                                    data-testid="toggle-password"
                                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                                >
                                    {showPassword ? '🙈' : '👁️'}
                                </button>
                            </div>
                        </div>

                        {/* Barra de intensida + checklist de fortaleza */}
                        <StrengthMeter password={passwordInput} />

                        {/* Botón submit — gradiente con hover/elevation */}
                        <button
                            type="button"
                            className="btn-submit"
                            onClick={handleLoginSubmit}
                            disabled={loading || !nifInput.trim() || passwordInput.length === 0}
                            data-testid="login-submit"
                        >
                            {loading ? 'Autenticando…' : 'Iniciar Sesión'}
                        </button>

                        {/* Aviso legal — compacto dentro del card */}
                        <div className="info-box">
                            <p>
                                📋 Necesita su NIF/Pasaporte y contraseña de matrícula.<br />
                                ¿Problemas? Consulte con la administración.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // ── Paso 3: loading visual ---
    return (
        <div className="login-page">
            <div className="login-card">
                <div className="loading-screen">
                    <div className="spinner" />
                    <p className="loading-text">Autenticando…</p>
                </div>
            </div>
        </div>
    );
}
