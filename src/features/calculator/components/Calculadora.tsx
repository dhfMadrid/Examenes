// Calculadora.tsx -- Desmos Graphing Calculator embebida, accesible durante el examen

interface CalculadoraProps {
  abierto: boolean;
  onClose: () => void;
}

/** Pane flotante que contiene la calculadora de Desmos. Se renderiza en fixed overlay sobre el examen. */
export default function Calculadora({ abierto, onClose }: CalculadoraProps) {
  if (!abierto) return null;

  const estilos = {
    container: {
      position: 'fixed' as const,
      top: 80,
      right: 16,
      width: 520,
      height: 460,
      display: 'flex' as const,
      flexDirection: 'column' as const,
      background: '#fff',
      border: '2px solid #333',
      borderRadius: 8,
      boxShadow: '0 4px 24px rgba(0,0,0,0.18)',
      zIndex: 9999,
      overflow: 'hidden' as const,
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '6px 12px',
      background: '#CFF',
      borderBottom: '1px solid #333',
      fontFamily: 'Arial, sans-serif',
    },
    title: {
      margin: 0,
      fontSize: 14,
      color: '#004080',
      fontWeight: 'bold',
    },
    closeBtn: {
      background: 'none',
      border: '1px solid #ccc',
      borderRadius: 3,
      padding: '2px 10px',
      cursor: 'pointer',
      fontSize: 14,
      fontWeight: 'bold',
    },
    iframeWrapper: {
      flex: 1,
      overflow: 'hidden',
    },
  };

  return (
    <div data-testid="calculadora-overlay" style={estilos.container}>
      {/* Barra superior */}
      <div style={estilos.header}>
        <h4 style={estilos.title}>Calculadora</h4>
        <button onClick={onClose} data-testid="btn-cerrar-calculadora" style={estilos.closeBtn}>
          ×
        </button>
      </div>

      {/* Iframe de Desmos */}
      <div style={estilos.iframeWrapper}>
        <iframe
          src="https://www.desmos.com/scientific?lang=es"
          width="100%"
          height="100%"
          frameBorder="0"
          allow="clipboard-write"
          title="Calculadora Desmos"
          style={{ display: 'block' }}
        />
      </div>
    </div>
  );
}
