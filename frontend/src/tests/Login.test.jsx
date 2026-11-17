import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Login from '../pages/Login';

describe('Página de Login (Proceso 1 - Seguridad OWASP y Accesibilidad)', () => {
  test('debe contener inputs con labels vinculados y type password', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const userInput = screen.getByLabelText(/RUT o Correo Electrónico/i);
    const passInput = screen.getByLabelText(/Contraseña/i);

    expect(userInput).toBeInTheDocument();
    expect(passInput).toBeInTheDocument();
    expect(passInput).toHaveAttribute('type', 'password');
  });

  test('debe auto-completar credenciales de prueba al hacer clic en los botones demo', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    );

    const btnCoordinador = screen.getByRole('button', { name: /^Coordinador$/i });
    fireEvent.click(btnCoordinador);

    const userInput = screen.getByLabelText(/RUT o Correo Electrónico/i);
    expect(userInput.value).toBe('11111111-1');
  });
});
