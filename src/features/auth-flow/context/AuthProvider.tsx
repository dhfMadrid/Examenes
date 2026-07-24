// AuthProvider.tsx — Provider funcional para auth (RN-AUT)
import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom';
import { AuthServiceProd, guardarJWT, obtenerJWT, cerrarSesionCliente, estaAutenticado } from '../domain/auth.api';
import { estaExpiradoJWT } from '../domain/auth.domain';
import type { AuthUser, MFACallbackType } from './AuthContext';
// Único contexto de verdad: un solo createContext desde AuthContext.tsx
import { AuthContext, useAuth } from './AuthContext';

// Re-exportar para compatibilidad con importaciones existentes de App.tsx y LoginPage.tsx
export { useAuth };
export type { MFACallbackType, AuthUser } from './AuthContext';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8001/api/v1' : '/api/v1');

function constructUser(token: string): AuthUser | null {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) return null;
        const payload = JSON.parse(atob(parts[1]));
        return {
            sub: payload.sub ?? '',
            nombre: payload.nombre ?? '',
            apellidos: payload.apellidos ?? '',
            nifPasaporte: payload.nifPasaporte ?? payload.sub ?? '',
            matriculaId: payload.matriculaId ?? '',
            licenciaDesc: payload.licenciaDesc ?? '',
        };
    } catch {
        return null;
    }
}

// useAuth se importa y re-exporta desde AuthContext.tsx — no duplicar.

interface AuthProviderProps {
    children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [usuario, setUsuario] = useState<AuthUser | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [estado, setEstado] = useState<'loading' | 'authenticated' | 'unauthenticated'>('loading');

    // On mount: check for persisted JWT (RN-AUT-05)
    useEffect(() => {
        const stored = obtenerJWT();
        if (stored && !estaExpiradoJWT(stored)) {
            const user = constructUser(stored);
            if (user) {
                setUsuario(user);
                setToken(stored);
                setEstado('authenticated');
                return;
            }
        }
        // Token no presente o expirado
        if (estaAutenticado()) {
            setToken(obtenerJWT()); // still have a token but expired — unauthenticated
            setEstado('unauthenticated');
        } else {
            setEstado('unauthenticated');
        }
    }, []);

    const cargarDatosUsuario = useCallback(async (nifPasaporte: string, tempToken: string) => {
        // Step 2 of login: send NIF + temporary token to get full JWT
        setEstado('loading');
        try {
            const client = new AuthServiceProd(API_BASE);
            client.setTempToken(tempToken);
            // Demo OTP válido (6 dígitos numéricos) — backend solo valida formato, no valor
            const demoOtp = '000001';
            const resp = await client.verifyMFA({ nifPasaporte, codigoMFA: demoOtp });
            if (resp.exitoso && resp.jwtToken) {
                guardarJWT(resp.jwtToken);
                setToken(resp.jwtToken);
                const user = constructUser(resp.jwtToken);
                if (user) {
                    setUsuario(user);
                }
                setEstado('authenticated');
                return true;
            }
            setEstado('unauthenticated');
            cerrarSesionCliente();
            return false;
        } catch {
            setEstado('unauthenticated');
            cerrarSesionCliente();
            return false;
        }
    }, []);

    const verificarMFA = useCallback(async (_codigo: string) => {
        if (!token || !usuario) return false;
        setEstado('loading');
        try {
            // For now, accept any valid OTP code as demo MFA
            // In production this would call POST /api/v1/auth/verify-otp with real code
            const storedJWT = obtenerJWT();
            if (storedJWT) {
                guardarJWT(storedJWT);
                setToken(storedJWT);
                setEstado('authenticated');
                return true;
            }
            return false;
        } catch {
            setEstado('unauthenticated');
            cerrarSesionCliente();
            return false;
        }
    }, [token, usuario]);

    const cerrarSesion = useCallback(() => {
        cerrarSesionCliente();
        setUsuario(null);
        setToken(null);
        setEstado('unauthenticated');
    }, []);

    // Periodically check token expiration (RN-AUT-05)
    useEffect(() => {
        if (!token || !estaAutenticado()) return;
        const interval = setInterval(() => {
            const stored = obtenerJWT();
            if (!stored || estaExpiradoJWT(stored)) {
                setUsuario(null);
                setToken(null);
                setEstado('unauthenticated');
                cerrarSesionCliente();
            }
        }, 10_000); // check every 10s
        return () => clearInterval(interval);
    }, [token]);

    // Demo modo: iniciar un usuario mock sin backend (RN-AUT-08)
    const iniciarModoDemo = useCallback(() => {
        const demoUser: AuthUser = {
            sub: '12345678Z',
            nombre: 'Demo',
            apellidos: 'Usuaria',
            nifPasaporte: '12345678Z',
            matriculaId: '',
            licenciaDesc: 'DEMO',
        };
        setUsuario(demoUser);
        setToken('demo-token');
        setEstado('authenticated');
    }, []);

    const value: MFACallbackType = {
        estado,
        usuario,
        token,
        cargarDatosUsuario,
        verificarMFA,
        iniciarModoDemo,
        cerrarSesion,
        actualizarSesionSincronizada(nifPasaporte: string, jwtToken: string): boolean | null {
            try {
                const parts = jwtToken.split('.');
                if (parts.length !== 3) {
                    console.error('[AuthProvider] Token mock: solo ' + parts.length + ' partes — intentando parse directo');
                }
                let payloadRaw: string;
                // Intentar decode base64 primero; si falla, usar JSON raw (tu backend mock lo envía así)
                try {
                    payloadRaw = atob(parts[1]);
                    console.log('[AuthProvider] JWT payload decoded via atob');
                } catch (_e) {
                    // Fallback: el mock de FastAPI usa JSON literal escapado en la posición [1]
                    payloadRaw = parts[1];
                    console.log('[AuthProvider] JWT payload usando raw (mock): ' + payloadRaw.substring(0, 60));
                }
                const parsed = JSON.parse(payloadRaw);
                console.log('[AuthProvider] ✅ payload sub=' + parsed.sub + ', nombre=' + parsed.nombre);
                const user: AuthUser = {
                    sub: String(parsed.sub ?? ''),
                    nombre: String(parsed.nombre ?? ''),
                    apellidos: String(parsed.apellidos ?? ''),
                    nifPasaporte: String(parsed.nifPasaporte ?? parsed.sub ?? nifPasaporte),
                    matriculaId: String(parsed.matriculaId ?? ''),
                    licenciaDesc: String(parsed.licenciaDesc ?? ''),
                };
                guardarJWT(jwtToken);
                ReactDOM.flushSync(() => {
                    setUsuario(user);
                    setToken(jwtToken);
                    setEstado('authenticated');
                });
                console.log('[AuthProvider] ✅ sesión sync actualizada — usuario=' + user.nifPasaporte);
                return true;
            } catch (e) {
                console.error('[AuthProvider] ❌ actualizarSionSync FAIL:', e);
                return null;
            }
        },

    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}