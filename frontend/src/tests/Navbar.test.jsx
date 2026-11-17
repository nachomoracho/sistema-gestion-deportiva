import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom';
import Navbar from '../components/Navbar';
import { authService } from '../services/authService';

jest.mock('../services/authService');

describe('Componente Navbar (Semántica HTML5 y Logout)', () => {
  test('debe mostrar botón de cerrar sesión para usuarios autenticados', () => {
    authService.isAuthenticated.mockReturnValue(true);
    authService.getCurrentUser.mockReturnValue({
      nombre: 'Carlos',
      apellido: 'Valenzuela',
      perfil: 'COORDINADOR',
    });

    render(
      <BrowserRouter>
        <Navbar />
      </BrowserRouter>
    );

    const logoutBtn = screen.getByRole('button', { name: /cerrar sesión/i });
    expect(logoutBtn).toBeInTheDocument();
    expect(screen.getByText(/Carlos Valenzuela/i)).toBeInTheDocument();
  });
});
