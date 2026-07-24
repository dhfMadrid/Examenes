// auth.api.ts — Servicio API para autenticación (cliente)
// Interfaz para el backend que implementará: POST /api/v1/auth/login, POST /api/v1/auth/mfa-verify

import type { ValidationResult } from "./auth.domain";

// ============================================================
// Tipos del DTO de autenticación
// ============================================================

export interface LoginRequest {
    nifPasaporte: string;
    password: string;
}

export interface LoginResponse {
    exitoso: boolean;
    requiereMFA: boolean;
    mensaje?: string;
    tokenTemporal?: string | null;
    jwtToken?: string | null;
}

export interface MFALoginPayload {
    nifPasaporte: string;
    codigoMFA: string;
}

export interface MFAResponse {
    exitoso: boolean;
    jwtToken: string | null;
    mensaje?: string;
}

// ============================================================
// Interfaz genérica de servicio de autenticación
// Permite mockear en tests sin hacer llamadas HTTP reales
// ============================================================

export interface AuthService {
    /** Envía credenciales al endpoint /auth/login */
    login(args: LoginRequest): Promise<LoginResponse>;
    /** Envía código MFA al endpoint /auth/mfa-verify */
    verifyMFA(payload: MFALoginPayload): Promise<LoginResponse>;
    /** Verifica credenciales localmente (offline validation) */
    validarLocalmente(nifPasaporte: string, password: string): ValidationResult;
    /** Genera un OTP temporal para la interfaz de usuario */
    generarOTPTemporal(): string;
}

// ============================================================
// Token helper functions
// ============================================================

const JWT_STORAGE_KEY = "examenesulm_jwt_token";
const LOGIN_TIMESTAMP_KEY = "examenesulm_login_timestamp";

/** Guarda el JWT en localStorage tras login exitoso */
export function guardarJWT(token: string): void {
    localStorage.setItem(JWT_STORAGE_KEY, token);
    localStorage.setItem(LOGIN_TIMESTAMP_KEY, String(Date.now()));
    
    // Disparar un evento para cualquier componente que deba reaccionar (ej. AuthProvider)
    window.dispatchEvent(new CustomEvent('jwt-stored', { detail: token }));
}

/** Obtiene el JWT almacenado (null si no existe) */
export function obtenerJWT(): string | null {
    return localStorage.getItem(JWT_STORAGE_KEY);
}

/** Elimina el JWT y limpia la sesión del cliente */
export function cerrarSesionCliente(): void {
    localStorage.removeItem(JWT_STORAGE_KEY);
    localStorage.removeItem(LOGIN_TIMESTAMP_KEY);
}

/** Comprueba si tenemos un token en localStorage (sesión activa) */
export function estaAutenticado(): boolean {
    return obtenerJWT() !== null;
}

/** Calcula los segundos desde el último login (0 si no hay sesión) */
export function tiempoDesdeUltimoLoginSegundos(): number | null {
    const ts = localStorage.getItem(LOGIN_TIMESTAMP_KEY);
    if (!ts) return null;
    const ahora = Date.now();
    const ultimo = parseInt(ts, 10);
    if (isNaN(ultimo)) return null;
    return Math.floor((ahora - ultimo) / 1000);
}

// ============================================================
// Servicio de producción: usa fetch API y la configuración real del backend
// ============================================================

export class AuthServiceProd implements AuthService {
    private baseUrl: string;
    private tokenTemporal: string | null = null; // temporal token after login step 1

    constructor(baseUrl: string | undefined = undefined) {
        // Usa .env si existe, sino fallback a absoluto al backend
        const envUrl = typeof import.meta !== 'undefined' && import.meta?.env?.VITE_API_BASE_URL;
        this.baseUrl = baseUrl ?? (envUrl ?? "/api/v1");
    }

    /** Sets the temporary MFA challenge token received in login response */
    setTempToken(token: string): void {
        this.tokenTemporal = token;
    }

    getTempToken(): string | null {
        return this.tokenTemporal;
    }

    async login(args: LoginRequest): Promise<LoginResponse> {
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (this.tokenTemporal) {
            headers["Authorization"] = `Bearer ${this.tokenTemporal}`;
        }

        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: "POST",
            headers,
            body: JSON.stringify(args),
        });

        if (!response.ok) {
            return { exitoso: false, requiereMFA: false, mensaje: `Error HTTP ${response.status}` };
        }

        const data = await response.json();
        return {
            exitoso: true,
            requiereMFA: data.requiereMFA ?? true,
            mensaje: data.mensaje,
            tokenTemporal: data.tokenTemporal || null,
        };
    }

    async verifyMFA(payload: MFALoginPayload): Promise<LoginResponse> {
        const response = await fetch(`${this.baseUrl}/auth/mfa-verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            return { exitoso: false, requiereMFA: true, mensaje: `Error HTTP ${response.status}`, tokenTemporal: null, jwtToken: null };
        }

        const data = await response.json();
        if (data.jwtToken) {
            guardarJWT(data.jwtToken);  // persiste en localStorage for future requests
        }

        return { exitoso: data.exitoso ?? true, requiereMFA: false, jwtToken: data.jwtToken || null, mensaje: data.mensaje };
    }

    validarLocalmente(nifPasaporte: string, password: string): ValidationResult {
        const { esIdentificadorValido, esPasswordFuerte } = require("./auth.domain");
        if (!esIdentificadorValido(nifPasaporte)) {
            return { valid: false, error: "Formato de NIF/Pasaporte incorrecto" };
        }
        if (!esPasswordFuerte(password)) {
            return { valid: false, error: "La contraseña no cumple los requisitos de seguridad (RN-AUT-03)" };
        }
        // No devolvemos la contraseña en el error — seguridad RN-SEG-01
        return { valid: true, error: null };
    }

    generarOTPTemporal(): string {
        const { generarOTP } = require("./auth.domain");
        return generarOTP();
    }
}
