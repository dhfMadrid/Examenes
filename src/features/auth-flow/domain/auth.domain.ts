// auth.domain.ts — Domain logic para autenticación y verificación MFA (RN-AUT-01 a RN-AUT-04)
// DNI español: 8 dígitos + letra de control calculada sobre módulo 23: TRWAGMYFPDXBNJZSQVHLCKE
export const LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE";

// ============================================================
// RN-AUT-01: Validar NIF/Pasaporte (ya existía, con test de regresión)
// ============================================================

export function validarDNI(nif: string): boolean {
    const regex = /^[0-9]{8}[A-Z]$/;
    if (!regex.test(nif)) return false;
    const numero = parseInt(nif.slice(0, 8), 10);
    return LETRAS_DNI[numero % 23] === nif[8];
}

export function validarPasaporte(nif: string): boolean {
    // Formato internacional: X/Y/Z + 7 dígitos + letra
    const regex = /^[XYZ][0-9]{7}[A-Z]$/;
    return regex.test(nif);
}

/** Valida cualquier NIF/Pasaporte válido en España (RN-AUT-01) */
export function esIdentificadorValido(id: string): boolean {
    if (!id || id.trim().length === 0) return false;
    const normalized = id.trim().toUpperCase();
    return validarDNI(normalized) || validarPasaporte(normalized);
}

// ============================================================
// RN-AUT-03: Validación de contraseña fuerte (NUEVO)
// ============================================================

export function esPasswordFuerte(password: string): boolean {
    // No null/undefined
    if (!password) return false;
    
    let hasMinLength = password.length >= 8;
    let tieneMinuscula = /[a-z]/.test(password);
    let tieneMayuscula = /[A-Z]/.test(password);
    let tieneDigito = /[0-9]/.test(password);

    return hasMinLength && tieneMinuscula && tieneMayuscula && tieneDigito;
}

// ============================================================
// RN-AUT-02: Validación completa de login (NUEVO)
// ============================================================

export interface ValidationResult {
    valid: boolean;
    error: string | null;
}

/** Valida NIF/Pasaporte + contraseña fuerte en un solo paso (RN-AUT-01 + RN-AUT-03) */
export function validarCredencialesLogin(nifPasaporte: string, password: string): ValidationResult {
    // Primero validamos el identificador
    if (!esIdentificadorValido(nifPasaporte)) {
        return { valid: false, error: "Formato de NIF/Pasaporte incorrecto" };
    }

    // Luego validamos la contraseña (RN-AUT-03)
    if (!esPasswordFuerte(password)) {
        return { valid: false, error: "La contraseña debe tener al menos 8 caracteres con mayúscula, minúscula y dígito" };
    }

    // Credenciales válidas para enviar al backend
    return { valid: true, error: null };
}

// ============================================================
// RN-AUT-04: Validación OTP (MFA) (NUEVO)
// ============================================================

/** Valida un código OTP de 6 dígitos numéricos */
export function validarOTP(codigo: string): boolean {
    if (!codigo || codigo.trim().length !== 6) return false;
    // Solo dígitos numéricos, sin espacios ni otros caracteres
    const regex = /^[0-9]{6}$/;
    return regex.test(codigo.trim());
}

/** Genera un OTP aleatorio de 6 dígitos */
export function generarOTP(): string {
    const random = Math.floor(Math.random() * 1000000); // 0-999999
    return String(random).padStart(6, "0");
}

// ============================================================
// RN-AUT-05: Funciones de token JWT simulado (NUEVO)
// ============================================================

interface JWTClaims {
    sub: string;
    roles: string[];
    exp: number; // epoch timestamp
    iat: number;
    [key: string]: any; // campos adicionales del claim
}

export function crearJWTClamasFake(claims: JWTClaims): string {
    const header = btoa(JSON.stringify({ alg: "RS256", typ: "JWT" }));
    const payload = btoa(JSON.stringify(claims));
    // En producción usaríamos firma real con crypto.subtle.sign()
    return `${header}.${payload}.fake_signature_do_not_use_in_production`;
}

export function decodificarJWTClaims(token: string): JWTClaims | null {
    try {
        const parts = token.split(".");
        if (parts.length !== 3) return null;
        let payloadStr: string;
        // Intentar decode base64 estándar JWT; si falla, fallback a JSON raw para mocks/fastapi
        try {
            payloadStr = atob(parts[1]);
        } catch (_atobErr) {
            // Fallback: backend mock envía JSON literal directo en partes[1] (no base64)
            payloadStr = parts[1];
        }
        const claims = JSON.parse(payloadStr);
        return claims as JWTClaims;
    } catch {
        return null;
    }
}

/** Verifica si el token ha expirado */
export function estaExpiradoJWT(token: string): boolean {
    const claims = decodificarJWTClaims(token);
    if (!claims) return true;
    const ahora = Math.floor(Date.now() / 1000); // segundos unix epoch
    return claims.exp !== undefined && claims.exp <= ahora;
}

/** Obtiene el tiempo de expiración restante en segundos */
export function expiracionRestanteSegundos(token: string): number {
    const claims = decodificarJWTClaims(token);
    if (!claims) return 0;
    if (claims.exp === undefined) return 0;
    const ahora = Math.floor(Date.now() / 1000); // segundos unix epoch
    return Math.max(0, claims.exp - ahora);
}
