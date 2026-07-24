// App.tsx — React SPA application (RN-AUT, RN-EST) con routing real
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './features/auth-flow/context/AuthProvider';
import LoginPage from './features/auth-flow/components/LoginPage';
import ExamSelectionPage from './features/exam-selection/pages/ExamSelectionPage';
import ExamSessionPage from './features/exam/pages/ExamSessionPage';
import ResultsPage from './features/results/pages/ResultsPage';

/** Ruta protegida: solo si está autenticado o en.demo mode */
function ProtectedRoute({ children }: React.PropsWithChildren<{ path?: string }>) {
    const auth = useAuth();
    const location = useLocation();
    console.log('[ProtectedRoute] estado=', auth.estado, 'token_presente=', !!auth.token, 'usuario=', auth.usuario?.sub ?? 'none', 'ruta=', location.pathname);

    if (auth.estado === 'loading') return <div data-testid="protected-loading">Cargando...</div>;
    if (auth.estado === 'authenticated') return <>{children}</>;
    
    // Demo mode: aceptar navigation state { dreamMode: true } del login page
    const navState = location.state as { dreamMode?: boolean } | null;
    if (navState?.dreamMode) return <>{children}</>;
    
    return <Navigate to="/" replace />;
}

/** Wrapper para ResultadosPage que captura examId desde navigation state */
function ResultsPageWrapper() {
    const location = useLocation();
    const examId = (location.state as { examId?: string } | null)?.examId;
    console.log('[ResultsPageWrapper] examId from state:', examId);
    return <ResultsPage examId={examId} />;
}

/** Componente raiz que mapea rutas */
export default function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<LoginPage />} />
            <Route
                path="/seleccion"
                element={
                    <ProtectedRoute>
                        <ExamSelectionPage />
                    </ProtectedRoute>
                }
            />
            {/* Examen activo: recibe examId por URL */}
            <Route
                path="/examen/:examId"
                element={
                    <ProtectedRoute>
                        <ExamSessionPage />
                    </ProtectedRoute>
                }
            />
            <Route
                path="/resultados"
                element={
                    <ProtectedRoute>
                        <ResultsPageWrapper />
                    </ProtectedRoute>
                }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
}
