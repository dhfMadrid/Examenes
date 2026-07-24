// AuthContext — React context para gestionar el estado de autenticación global

import React from 'react';

export interface AuthUser {
    sub: string;
    nombre: string;
    apellidos: string;
    nifPasaporte: string;
    matriculaId: string;
    licenciaDesc: string;
}

export type AuthState = 'loading' | 'authenticated' | 'unauthenticated';

export type MFACallbackType = {
    estado: AuthState;
    usuario: AuthUser | null;
    token: string | null;
    cargarDatosUsuario(nifPasaporte: string, tempToken: string): Promise<boolean>;
    verificarMFA(codigo: string): Promise<boolean>;
    iniciarModoDemo(): void;
    cerrarSesion(): void;
    /** Actualiza sesión sincrónicamente tras login (sin Async) */
    actualizarSesionSincronizada(nifPasaporte: string, jwtToken: string): boolean | null;
};

export const AuthContext = React.createContext<MFACallbackType>({
    estado: 'loading',
    usuario: null,
    token: null,
    cargarDatosUsuario: async (_a: string, _b: string) => Promise.resolve(true),
    verificarMFA: async (_codigo: string) => Promise.resolve(true),
    iniciarModoDemo: () => {},
    cerrarSesion: () => {},
    actualizarSesionSincronizada(): boolean | null { return null; },
});

/** Hook simplificado para consumir auth state */
export function useAuth(): MFACallbackType {
    return React.useContext(AuthContext);
}
