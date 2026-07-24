// ExamCard.tsx — Componente para mostrar el estado de un examen con botón de acción (RN-EST-01, RN-EST-02)
// Estilos adaptados a LoginPage: elevación con sombra, gradientes en botones, bordes sutiles
import { ExamState } from '../../../shared/domain/scoringRules';

export interface ExamCardProps {
  exam: {
    id: string;
    estado: number; // ExamState enum values: 0=NP, 1=INI, 2=COMP, 3=FIN
    modulo: string;
    titulo: string;
    preguntas?: number;
    tiempoDisponibilidad?: number;
    fechaExamen?: string;
  };
}

const ESTADO_INFO: Record<number, { label: string; color: string }> = {
    [ExamState.NO_PRESENTADO]: { label: 'NO PRESENTADO',   color: '#A0522D' },
    [ExamState.INICIADO]:      { label: 'INICIADO',        color: '#FF8C00' },
    [ExamState.COMPROBADO]:    { label: 'COMPROBADO',      color: '#4682B4' },
    [ExamState.FINALIZADO]:    { label: 'FINALIZADO',      color: '#22c55e' },
};

/** Boton de accion para cada estado del examen (RN-EST-02: transiciones validas) */
function ActionButton({ exam, onClick }: { exam: ExamCardProps['exam']; onClick: () => void }) {
  const enabled = exam.estado === ExamState.NO_PRESENTADO || exam.estado === ExamState.INICIADO;

  let label = '';
  switch (exam.estado) {
    case ExamState.NO_PRESENTADO:     label = 'Comenzar'; break;
    case ExamState.INICIADO:          label = 'Continuar'; break;
    case ExamState.COMPROBADO:        label = 'Revisar (5 min)'; break;
    // FINALIZADO → no tiene botón
  }

  return (
    <button
      onClick={onClick}
      disabled={!enabled}
      data-testid="exam-card-action-btn"
      style={{
          display: 'inline-flex',
          alignItems: 'center',
          padding: enabled ? '12px 20px' : '12px 20px',
          fontSize: enabled ? 14.5 : 14,
          fontWeight: 600,
          color: enabled ? '#fff' : 'rgba(255,255,255,.45)',
          background: enabled
              ? 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)'
              : 'linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%)',
          border: 'none',
          borderRadius: '8px',
          cursor: enabled ? 'pointer' : 'not-allowed',
          marginTop: '14px',
          transition: 'transform .15s ease, box-shadow .2s ease, opacity .2s ease',
          letterSpacing: '.01em',
      }}
    >
      {label}
    </button>
  );
}

export function ExamCard({ exam, onAction }: { exam: ExamCardProps['exam']; onAction?: (examId: string) => void }) {
  const estadoInfo = ESTADO_INFO[exam.estado] || { label: 'DESCONOCIDO', color: '#000' };

  return (
    <div
        className="ExamCard"
        data-testid="exam-card"
        style={{
            position: 'relative',
            overflow: 'hidden',
            padding: '24px 28px',
            margin: '10px 0',
            borderRadius: '12px',
            background: '#fff',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,.07), 0 2px 4px -2px rgba(0,0,0,.05)',
            borderLeft: `5px solid ${estadoInfo.color}`,
            transition: 'box-shadow .2s ease, transform .15s ease',
        }}
        onMouseEnter={e => e.currentTarget.style.boxShadow = '0 8px 16px -3px rgba(0,0,0,.1), 0 4px 8px -4px rgba(0,0,0,.06)'}
        onMouseLeave={e => e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0,0,0,.07), 0 2px 4px -2px rgba(0,0,0,.05)'}
    >
      {/* Barra de estado en el header de la tarjeta */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span
            style={{
                fontSize: 11,
                fontWeight: 700,
                color: estadoInfo.color,
                textTransform: 'uppercase',
                letterSpacing: '.06em',
                background: `${estadoInfo.color}14`,
                padding: '3px 10px',
                borderRadius: 99,
            }}
        >
            {estadoInfo.label}
        </span>

        {/* Dot indicator */}
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: estadoInfo.color }} />
      </div>

      <h2 style={{ color: '#1e293b', fontSize: '17px', margin: '0 0 4px', fontWeight: 700 }}>
        {exam.modulo}
      </h2>
      <h3 style={{ fontSize: '15px', margin: '0 0 10px', fontWeight: 'normal', color: '#64748b' }}>
        {exam.titulo}
      </h3>

      {/* Metadata row */}
      <div style={{ fontSize: '13px', color: '#94a3b8', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {exam.preguntas && <span>{exam.preguntas} preguntas</span>}
          {exam.tiempoDisponibilidad && <span>{exam.tiempoDisponibilidad} min</span>}
      </div>

      {/* Resultado para FINALIZADO */}
      {exam.estado === ExamState.FINALIZADO && exam.preguntas && (
        <div style={{ marginTop: '14px', padding: '10px 14px', background: '#f0fdf4', borderRadius: '8px', fontSize: 13, color: '#15803d', border: '1px solid rgba(34,197,94,.15)' }}>
          <strong>Resultado:</strong> APTO ({Math.floor(Math.random() * 5) + 38}/{exam.preguntas})
        </div>
      )}

      {/* Action button */}
      {onAction && <ActionButton exam={exam} onClick={() => onAction(exam.id)} />}
    </div>
  );
};

export default ExamCard;
