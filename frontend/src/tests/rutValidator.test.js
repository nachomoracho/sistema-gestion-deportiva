import { validarRut, formatearRut, limpiarRut } from '../utils/rutValidator';

describe('Validador de RUT Módulo 11 (Frontend)', () => {
  test('debe validar RUTs chilenos correctos', () => {
    expect(validarRut('11111111-1')).toBe(true);
    expect(validarRut('22222222-2')).toBe(true);
    expect(validarRut('33333333-3')).toBe(true);
    expect(validarRut('18456789-K')).toBe(true);
    expect(validarRut('12345678-5')).toBe(true);
  });

  test('debe rechazar RUTs con dígito verificador incorrecto', () => {
    expect(validarRut('11111111-9')).toBe(false);
    expect(validarRut('22222222-0')).toBe(false);
  });

  test('debe limpiar caracteres no válidos', () => {
    expect(limpiarRut('11.111.111-1')).toBe('111111111');
    expect(limpiarRut('12.345.678-k')).toBe('12345678K');
  });

  test('debe formatear correctamente con puntos y guion', () => {
    expect(formatearRut('111111111')).toBe('11.111.111-1');
  });
});
