import React from 'react';

const EnDesarrolloModal = ({ show, onClose, titulo = 'Funcionalidad en Desarrollo', descripcion, payloadAdapter }) => {
  if (!show) return null;

  return (
    <div
      className="modal fade show d-block"
      tabIndex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-en-desarrollo-title"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.65)' }}
    >
      <div className="modal-dialog modal-dialog-centered modal-lg" role="document">
        <div className="modal-content shadow-lg border-0">
          <div className="modal-header bg-primary text-white">
            <h5 className="modal-title d-flex align-items-center gap-2" id="modal-en-desarrollo-title">
              <span className="badge bg-warning text-dark">Próxima Fase</span>
              {titulo}
            </h5>
            <button
              type="button"
              className="btn-close btn-close-white"
              aria-label="Cerrar ventana emergente"
              onClick={onClose}
            />
          </div>
          <div className="modal-body p-4">
            <div className="alert alert-info d-flex align-items-center mb-3" role="alert">
              <div>
                <strong>Aviso de Evolución Tecnológica:</strong> Esta característica corresponde a una extensión proyectada para el siguiente ciclo de despliegue. Todos los controles de seguridad y contratos de interoperabilidad han sido formulados bajo el patrón <code>Adapter</code>.
              </div>
            </div>

            <p className="text-secondary">
              {descripcion || 'La integración con la Intranet Académica Centralizada se encuentra modelada bajo el patrón Adapter (IntranetAcademicaAdapter). A continuación se exhibe la carga JSON estandarizada generada por el backend lista para consumo:'}
            </p>

            {payloadAdapter && (
              <div className="bg-light p-3 rounded border">
                <h6 className="text-muted mb-2">Payload Interoperable Generado (JSON):</h6>
                <pre className="m-0 text-dark small" style={{ maxHeight: '240px', overflowY: 'auto' }}>
                  {JSON.stringify(payloadAdapter, null, 2)}
                </pre>
              </div>
            )}
          </div>
          <div className="modal-footer bg-light">
            <button
              type="button"
              className="btn btn-secondary px-4"
              onClick={onClose}
            >
              Entendido
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnDesarrolloModal;
