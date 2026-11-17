import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { authService } from '../services/authService';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const usuario = authService.getCurrentUser();
  const rol = usuario?.perfil;

  const handleLogout = async () => {
    await authService.logout();
    navigate('/login');
  };

  if (!authService.isAuthenticated() || location.pathname === '/login') {
    return null;
  }

  const getRoleBadge = () => {
    switch (rol) {
      case 'COORDINADOR':
        return <span className="badge bg-danger">Coordinador</span>;
      case 'ENTRENADOR':
        return <span className="badge bg-success">Entrenador</span>;
      case 'ESTUDIANTE':
        return <span className="badge bg-info text-dark">Estudiante</span>;
      default:
        return null;
    }
  };

  return (
    <header>
      <nav className="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm px-3" aria-label="Navegación principal del sistema">
        <div className="container-fluid">
          <Link className="navbar-brand fw-bold d-flex align-items-center gap-2" to="/">
            <span className="badge bg-primary fs-6">SGAD</span>
            <span>Gestión Deportiva</span>
          </Link>

          <button
            className="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarContent"
            aria-controls="navbarContent"
            aria-expanded="false"
            aria-label="Alternar navegación"
          >
            <span className="navbar-toggler-icon"></span>
          </button>

          <div className="collapse navbar-collapse" id="navbarContent">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              {rol === 'COORDINADOR' && (
                <>
                  <li className="nav-item">
                    <Link
                      className={`nav-link ${location.pathname === '/coordinador' ? 'active fw-semibold' : ''}`}
                      to="/coordinador"
                    >
                      Panel de Control
                    </Link>
                  </li>
                  <li className="nav-item">
                    <Link
                      className={`nav-link ${location.pathname === '/reportes' ? 'active fw-semibold' : ''}`}
                      to="/reportes"
                    >
                      Reportería y Analítica
                    </Link>
                  </li>
                </>
              )}

              {rol === 'ENTRENADOR' && (
                <li className="nav-item">
                  <Link
                    className={`nav-link ${location.pathname === '/entrenador' ? 'active fw-semibold' : ''}`}
                    to="/entrenador"
                  >
                    Control en Cancha (Móvil)
                  </Link>
                </li>
              )}

              {rol === 'ESTUDIANTE' && (
                <li className="nav-item">
                  <Link
                    className={`nav-link ${location.pathname === '/estudiante' ? 'active fw-semibold' : ''}`}
                    to="/estudiante"
                  >
                    Mi Portal Deportivo
                  </Link>
                </li>
              )}
            </ul>

            <div className="d-flex align-items-center gap-3">
              <div className="text-light small text-end d-none d-sm-block">
                <div className="fw-semibold">{usuario?.nombre} {usuario?.apellido}</div>
                <div className="d-flex justify-content-end gap-1 mt-1">{getRoleBadge()}</div>
              </div>

              <button
                type="button"
                className="btn btn-outline-danger btn-sm d-flex align-items-center gap-1 px-3"
                onClick={handleLogout}
                aria-label="Cerrar sesión de usuario"
                id="btn-logout"
              >
                <span>Cerrar Sesión</span>
              </button>
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Navbar;
