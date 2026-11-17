import React from 'react';

const Footer = () => {
  return (
    <footer className="bg-light border-top py-3 mt-auto text-secondary small" role="contentinfo">
      <div className="container text-center">
        <p className="mb-1">
          <strong>Sistema Centralizado de Gestión de Actividades Deportivas (SGAD)</strong> &copy; {new Date().getFullYear()}
        </p>
        <p className="mb-0 text-muted" style={{ fontSize: '0.8rem' }}>
          Cumplimiento Ley N&deg; 21.459 (Delitos Informáticos), Ley N&deg; 19.628 (Protección de la Vida Privada) y Estándar ISO/IEC 27001 / 27002.
        </p>
      </div>
    </footer>
  );
};

export default Footer;
