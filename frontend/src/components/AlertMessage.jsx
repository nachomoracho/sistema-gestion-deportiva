import React from 'react';

const AlertMessage = ({ message, variant = 'danger', onClose, id }) => {
  if (!message) return null;

  return (
    <div
      id={id}
      className={`alert alert-${variant} alert-dismissible fade show my-3 d-flex align-items-center shadow-sm`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex-grow-1">
        <strong>{variant === 'danger' ? 'Atención: ' : variant === 'success' ? 'Éxito: ' : 'Información: '}</strong>
        {message}
      </div>
      {onClose && (
        <button
          type="button"
          className="btn-close"
          aria-label="Cerrar notificación"
          onClick={onClose}
        />
      )}
    </div>
  );
};

export default AlertMessage;
