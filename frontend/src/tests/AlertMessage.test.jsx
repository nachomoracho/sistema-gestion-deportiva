import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import AlertMessage from '../components/AlertMessage';

describe('Componente AlertMessage (Accesibilidad y UX)', () => {
  test('debe renderizar mensaje con rol de alerta para lectores de pantalla', () => {
    render(<AlertMessage message="Credenciales inválidas" variant="danger" />);
    
    const alertElement = screen.getByRole('alert');
    expect(alertElement).toBeInTheDocument();
    expect(alertElement).toHaveTextContent('Credenciales inválidas');
    expect(alertElement).toHaveClass('alert-danger');
  });

  test('no debe renderizar nada si el mensaje es nulo o vacío', () => {
    const { container } = render(<AlertMessage message="" />);
    expect(container.firstChild).toBeNull();
  });
});
