// LoginForm.tsx — Formulario de login: NIF/Pasaporte + contraseña (RN-AUT-01, RN-AUT-03)
import React, { useState } from "react";
import type { AuthUser } from "../context/AuthContext";
import { validarCredencialesLogin, esIdentificadorValido } from "../domain/auth.domain";

export interface LoginFormProps {
    onAuthSuccess: (usuario: AuthUser) => void;
    loading?: boolean;
}

function PasswordStrengthBar({ password }: { password: string }) {
    const checks = [
        { id: "len", label: "8+ caracteres", ok: password.length >= 8 },
        { id: "mai", label: "Mayúscula", ok: /[A-Z]/.test(password) },
        { id: "min", label: "Minúscula", ok: /[a-z]/.test(password) },
        { id: "dig", label: "Dígito", ok: /[0-9]/.test(password) },
    ];

    return (
        <ul style={{ listStyle: "none", padding: 0, margin: "8px 0", fontSize: 12 }}>
            {checks.map(c => (
                <li key={c.id} style={{ color: c.ok ? "#32CD32" : "#999", marginBottom: 2 }}>
                    {"\u2610"} {c.label}
                </li>
            ))}
        </ul>
    );
}

export const LoginForm: React.FC<LoginFormProps> = ({ onAuthSuccess, loading }) => {
    const [nifInput, setNifInput] = useState("12345678Z");
    const [passwordInput, setPasswordInput] = useState("Demo1234");
    const [error, setError] = useState<string | null>(null);
    const [showPassword, setShowPassword] = useState(false);

    // Validación en tiempo real (RN-AUT-03)
    const credValidas = validarCredencialesLogin(nifInput.trim(), passwordInput);
    const identValido = esIdentificadorValido(nifInput.trim());

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!credValidas.valid) {
            setError(credValidas.error ?? "Credenciales inválidas");
            return;
        }

        // Backend no implementado aún → simulamos login exitoso
        const mockUser: AuthUser = {
            sub: nifInput.trim().toUpperCase(),
            nombre: "Alumno",
            apellidos: "Mock",
            nifPasaporte: nifInput.toUpperCase().trim(),
            matriculaId: "MAT-001",
            licenciaDesc: "Licencia A3",
        };
        onAuthSuccess(mockUser);
    };

    return (
        <form onSubmit={handleSubmit} data-testid="login-form">
            <h2>Exámenes ULM Virtual</h2>

            {error && (<div data-testid="login-error">{error}</div>)}

            {/* Campo NIF/Pasaporte (RN-AUT-01) */}
            <label>NIF / Pasaporte</label>
            <input
                type="text"
                value={nifInput}
                onChange={e => { setNifInput(e.target.value); setError(null); }}
                placeholder="DNI / NIF de alumno (ej. 12345678Z)"
                data-testid="nif-input"
            />
            <small style={{ color: identValido ? "#32CD32" : "#999" }}>
                {nifInput.trim().length > 0 && identValido ? "Formato válido" : ""}
            </small>

            {/* Campo Contraseña (RN-AUT-03) */}
            <label style={{ marginTop: 16, display: "block" }}>Contraseña</label>
            <div style={{ position: 'relative' }}>
                <input
                    type={showPassword ? "text" : "password"}
                    value={passwordInput}
                    onChange={e => { setPasswordInput(e.target.value); setError(null); }}
                    placeholder="Contraseña (ej. Demo1234)"
                    data-testid="password-input"
                />
                <button
                    type="button"
                    onClick={() => setShowPassword(v => !v)}
                    style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', fontSize: 14 }}
                    data-testid="toggle-password"
                >
                    {showPassword ? '🙈' : '👁️'}
                </button>
            </div>

            {/* Feedback de fortaleza */}
            <PasswordStrengthBar password={passwordInput} />

            <button type="submit" disabled={loading || !credValidas.valid} data-testid="login-submit">
                {loading ? "Autenticando..." : "Iniciar Sesión"}
            </button>
        </form>
    );
};

export default LoginForm;
