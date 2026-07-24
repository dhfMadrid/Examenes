// AuthGuard.tsx — Guard de rutas para autenticación (RN-AUT)
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthProvider';

interface AuthGuardProps {
    children: React.ReactNode;
}

/** Rutas que NO requieren autenticación */
const PUBLIC_PATHS = ['/login', '/'];

function useIsPublicPath(pathname: string): boolean {
    return PUBLIC_PATHS.some(p => pathname.startsWith(p));
}

export function AuthGuard({ children }: AuthGuardProps) {
    const { estado } = useAuth();
    const location = useLocation();

    if (estado === 'loading') {
        return (
            <div data-testid="auth-guard-loading" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <p>Cargando...</p>
            </div>
        );
    }

    if (estado === 'unauthenticated') {
        // Only redirect to login if not already on a public path
        if (!useIsPublicPath(location.pathname)) {
            return <Navigate to="/login" state={{ from: location }} replace />;
        }
        // If on public path and unauthenticated, allow access (e.g., /login page)
    }

    if (estado === 'authenticated' && useIsPublicPath(location.pathname)) {
        // Already logged in — redirect away from login to dashboard
        return <Navigate to="/seleccion" replace />;
    }

    return <>{children}</>;
}

export function ProtectedRoute({ children }: AuthGuardProps) {
    const { estado } = useAuth();

    if (estado === 'loading') {
        return (
            <div data-testid="protected-route-loading" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <p>Cargando...</p>
            </div>
        );
    }

    if (estado !== 'authenticated') {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
}
