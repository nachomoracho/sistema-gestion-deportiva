/**
 * Utilidad de validación y formateo de RUT chileno bajo algoritmo Módulo 11.
 */

export const limpiarRut = (rut) => {
  if (!rut) return '';
  return rut.toString().replace(/[^0-9kK]/g, '').toUpperCase();
};

export const formatearRut = (rut) => {
  const limpio = limpiarRut(rut);
  if (limpio.length <= 1) return limpio;

  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);

  // Formatear cuerpo con puntos
  let cuerpoFormateado = '';
  let count = 0;
  for (let i = cuerpo.length - 1; i >= 0; i--) {
    cuerpoFormateado = cuerpo[i] + cuerpoFormateado;
    count++;
    if (count % 3 === 0 && i !== 0) {
      cuerpoFormateado = '.' + cuerpoFormateado;
    }
  }

  return `${cuerpoFormateado}-${dv}`;
};

export const validarRut = (rut) => {
  const limpio = limpiarRut(rut);
  if (limpio.length < 8 || limpio.length > 9) return false;

  const cuerpo = limpio.slice(0, -1);
  const dv = limpio.slice(-1);

  if (!/^\d+$/.test(cuerpo)) return false;

  let suma = 0;
  let multiplo = 2;

  for (let i = cuerpo.length - 1; i >= 0; i--) {
    suma += parseInt(cuerpo.charAt(i), 10) * multiplo;
    multiplo = multiplo < 7 ? multiplo + 1 : 2;
  }

  const resto = suma % 11;
  const dvEsperado = 11 - resto;

  let dvCalculado = '';
  if (dvEsperado === 11) dvCalculado = '0';
  else if (dvEsperado === 10) dvCalculado = 'K';
  else dvCalculado = dvEsperado.toString();

  return dv === dvCalculado;
};
