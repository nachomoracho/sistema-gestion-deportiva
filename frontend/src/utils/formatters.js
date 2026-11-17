/**
 * Formateadores de fecha, notas y evaluación de riesgo de asistencia.
 */

export const formatearFecha = (fechaStr) => {
  if (!fechaStr) return '-';
  try {
    const [year, month, day] = fechaStr.split('-');
    return `${day}/${month}/${year}`;
  } catch {
    return fechaStr;
  }
};

export const formatearHora = (horaStr) => {
  if (!horaStr) return '-';
  return horaStr.slice(0, 5); // '10:00'
};

export const formatearNota = (nota) => {
  if (nota === null || nota === undefined) return 'Sin nota';
  const num = parseFloat(nota);
  return isNaN(num) ? 'N/A' : num.toFixed(1);
};

export const getEstadoAsistenciaBadge = (porcentaje) => {
  if (porcentaje >= 75) {
    return {
      clase: 'badge bg-success',
      texto: 'Cumple asistencia reglamentaria (Aprobado)',
      variante: 'success',
      enRiesgo: false,
    };
  }
  if (porcentaje >= 60) {
    return {
      clase: 'badge bg-warning text-dark',
      texto: 'Riesgo académico moderado (Atención)',
      variante: 'warning',
      enRiesgo: true,
    };
  }
  return {
    clase: 'badge bg-danger',
    texto: 'Crítico: Riesgo de reprobación por inasistencia',
    variante: 'danger',
    enRiesgo: true,
  };
};
