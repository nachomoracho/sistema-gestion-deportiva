import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Login from './pages/Login';
import DashboardCoordinador from './pages/DashboardCoordinador';
import PanelEntrenadorMobile from './pages/PanelEntrenadorMobile';
import PortalEstudiante from './pages/PortalEstudiante';
import ReporteriaAvanzada from './pages/ReporteriaAvanzada';
import { authService } from './services/authService';

const ProtectedRoute = ({ children, allowedRoles }) => {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  const rol = authService.getUserRole();
  if (allowedRoles && !allowedRoles.includes(rol)) {
    // Redirigir al dashboard según su rol legítimo
    if (rol === 'COORDINADOR') return <Navigate to="/coordinador" replace />;
    if (rol === 'ENTRENADOR') return <Navigate to="/entrenador" replace />;
    if (rol === 'ESTUDIANTE') return <Navigate to="/estudiante" replace />;
    return <Navigate to="/login" replace />;
  }

  return children;
};

const RootRedirect = () => {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  const rol = authService.getUserRole();
  if (rol === 'COORDINADOR') return <Navigate to="/coordinador" replace />;
  if (rol === 'ENTRENADOR') return <Navigate to="/entrenador" replace />;
  if (rol === 'ESTUDIANTE') return <Navigate to="/estudiante" replace />;
  return <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <div className="d-flex flex-column min-vh-100 bg-light">
        <Navbar />
        <div className="flex-grow-1">
          <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route
              path="/coordinador"
              element={
                <ProtectedRoute allowedRoles={['COORDINADOR']}>
                  <DashboardCoordinador />
                </ProtectedRoute>
              }
            />

            <Route
              path="/reportes"
              element={
                <ProtectedRoute allowedRoles={['COORDINADOR']}>
                  <ReporteriaAvanzada />
                </ProtectedRoute>
              }
            />

            <Route
              path="/entrenador"
              element={
                <ProtectedRoute allowedRoles={['ENTRENADOR']}>
                  <PanelEntrenadorMobile />
                </ProtectedRoute>
              }
            />

            <Route
              path="/estudiante"
              element={
                <ProtectedRoute allowedRoles={['ESTUDIANTE']}>
                  <PortalEstudiante />
                </ProtectedRoute>
              }
            />

            <Route path="/" element={<RootRedirect />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
