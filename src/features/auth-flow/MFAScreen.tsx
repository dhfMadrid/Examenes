// MFAScreen.tsx — Pantalla de verificación MFA (RN-AUT-04)
import React, { useState } from "react";
import './components/LoginPage.css';

/* ═══════════════ Flujo único: input directo del código ── */
function MfaInput({ onVerifySuccess, onBack }: {
    onVerifySuccess: (codigo: string) => void;
    onBack: () => void;
}) {
    const [codigo, setCodigo] = useState("00000");

    return (
        <>
            {/* Header */}
            <div className="login-card-header">
                <span className="mfa-icon-large">&#x1F510;</span>
                <h2>Verificación de seguridad</h2>
                <p>Comprueba el código enviado a tu correo registrado</p>
            </div>

            {/* Body */}
            <div className="login-card-body">
                <p style={{ margin: '0 0 14px', color: 'var(--login-text-secondary)', fontSize: 14, lineHeight: 1.5 }}>
                    Introduce el código de 6 dígitos que recibiste por correo.<br />
                    Válido por 5 minutos.
                </p>

                <div className="otp-input-field-wrap">
                    <input
                        type="text"
                        value={codigo}
                        onChange={e => { setCodigo(e.target.value); }}
                        maxLength={6}
                        placeholder="00000"
                        inputMode="numeric"
                        pattern="[0-9]{6}"
                        className="input otp-input"
                        data-testid="mfa-otp-input"
                    />
                </div>

                <div style={{ marginTop: 24 }} className="flow-btn-row">
                    <button type="button" onClick={onBack} className="btn btn-back">
                        &#x2190; Volver al login
                    </button>
                    <button
                        type="button"
                        disabled={codigo.length !== 6 || !/^\d{6}$/.test(codigo)}
                        onClick={() => { onVerifySuccess(codigo); }}
                        className="btn btn-submit full-width"
                    >
                        Verificar
                    </button>
                </div>

                <p style={{ marginTop: 14, marginBottom: 0, textAlign: 'center', fontSize: 13, color: 'var(--login-text-muted)' }}>
                    ¿No recibiste el correo?{' '}
                    <a href="#resend" className="link-secondary">Reenviar código</a>
                </p>
            </div>
        </>
    );
}

/* ═══════════════ Flujo principal ── */
export interface MFAScreenProps {
    nifPasaporte?: string;
    onVerifySuccess: (codigoMFA: string) => void;
    onBack: () => void;
    isLoading?: boolean;
}

/** Pantalla completa de MFA con input directo */
export const MFAScreen: React.FC<MFAScreenProps> = ({
    onVerifySuccess, onBack, isLoading
}) => {
    return (
        <>
            <MfaInput onVerifySuccess={onVerifySuccess} onBack={onBack} />

            {/* ── Mensaje de carga (mientras backend responde) ── */}
            {isLoading && (
                <div className="loading-screen">
                    <div className="spinner" />
                    <p className="loading-text">Verificando código...</p>
                </div>
            )}
        </>
    );
};

export default MFAScreen;
