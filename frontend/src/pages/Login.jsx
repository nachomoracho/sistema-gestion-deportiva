import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import AlertMessage from '../components/AlertMessage';

const Login = () => {
  const navigate = useNavigate();
  const [identificador, setIdentificador] = useState('');
  const [clave, setClave] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Manejo de cambio de clave obligatorio
  const [showChangePassModal, setShowChangePassModal] = useState(false);
  const [nuevaClave, setNuevaClave] = useState('');
  const [confirmarClave, setConfirmarClave] = useState('');
  const [passChangeError, setPassChangeError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');

    if (!identificador.trim() || !clave) {
      setErrorMsg('Por favor complete todos los campos requeridos.');
      return;
    }

    setLoading(true);
    try {
      const usuario = await authService.login(identificador.trim(), clave);

      if (usuario.debe_cambiar_clave) {
        setShowChangePassModal(true);
        setLoading(false);
        return;
      }

      redirigirPorRol(usuario.perfil);
    } catch (err) {
      setErrorMsg(err.message || 'Error al autenticar.');
    } finally {
      setLoading(false);
    }
  };

  const redirigirPorRol = (perfil) => {
    switch (perfil) {
      case 'COORDINADOR':
        navigate('/coordinador');
        break;
      case 'ENTRENADOR':
        navigate('/entrenador');
        break;
      case 'ESTUDIANTE':
        navigate('/estudiante');
        break;
      default:
        navigate('/');
    }
  };

  const handleQuickFill = (userType) => {
    if (userType === 'coordinador') {
      setIdentificador('11111111-1');
      setClave('Admin2026!#Segura');
    } else if (userType === 'entrenador') {
      setIdentificador('22222222-2');
      setClave('Coach2026!#Segura');
    } else if (userType === 'estudiante') {
      setIdentificador('33333333-3');
      setClave('Alumno2026!#Segura');
    }
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    setPassChangeError('');

    if (nuevaClave !== confirmarClave) {
      setPassChangeError('Las contraseñas no coinciden.');
      return;
    }

    try {
      await authService.changePassword(clave, nuevaClave);
      setSuccessMsg('Contraseña actualizada con éxito. Iniciando sesión...');
      setShowChangePassModal(false);
      const user = authService.getCurrentUser();
      setTimeout(() => redirigirPorRol(user?.perfil), 1000);
    } catch (err) {
      setPassChangeError(err.message || 'Error al actualizar contraseña.');
    }
  };

  return (
    <main className="container d-flex align-items-center justify-content-center min-vh-100 py-4">
      <div className="card shadow-lg border-0 w-100" style={{ maxWidth: '440px' }}>
        <div className="card-header bg-dark text-white text-center py-4">
          <span className="badge bg-primary px-3 py-2 fs-6 mb-2">SGAD</span>
          <h1 className="h4 mb-1">Gestión Deportiva</h1>
          <p className="text-light small mb-0">Portal Centralizado Institucional</p>
        </div>

        <div className="card-body p-4">
          <AlertMessage message={errorMsg} variant="danger" onClose={() => setErrorMsg('')} />
          <AlertMessage message={successMsg} variant="success" onClose={() => setSuccessMsg('')} />

          <form onSubmit={handleSubmit} noValidate>
            <div className="mb-3">
              <label htmlFor="login-identificador" className="form-label fw-semibold">
                RUT o Correo Electrónico
              </label>
              <input
                type="text"
                className="form-control form-control-lg"
                id="login-identificador"
                name="identificador"
                autoComplete="username"
                placeholder="Ej. 11111111-1 o usuario@deportes.cl"
                value={identificador}
                onChange={(e) => setIdentificador(e.target.value)}
                required
                aria-required="true"
              />
              <div className="form-text">Sin puntos y con guion (ej. 12345678-5)</div>
            </div>

            <div className="mb-4">
              <label htmlFor="login-clave" className="form-label fw-semibold">
                Contraseña
              </label>
              <input
                type="password"
                className="form-control form-control-lg"
                id="login-clave"
                name="clave"
                autoComplete="current-password"
                placeholder="Ingrese su contraseña"
                value={clave}
                onChange={(e) => setClave(e.target.value)}
                required
                aria-required="true"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg w-100 fw-bold shadow-sm"
              disabled={loading}
              id="btn-login-submit"
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Validando credenciales...
                </>
              ) : (
                'Iniciar Sesión'
              )}
            </button>
          </form>

          {/* Accesos rápidos de prueba */}
          <section className="mt-4 pt-3 border-top" aria-label="Cuentas de demostración">
            <p className="small text-muted fw-bold mb-2 text-center">Cuentas demo para evaluación:</p>
            <div className="d-flex justify-content-between gap-1">
              <button
                type="button"
                className="btn btn-outline-secondary btn-sm flex-fill"
                onClick={() => handleQuickFill('coordinador')}
              >
                Coordinador
              </button>
              <button
                type="button"
                className="btn btn-outline-secondary btn-sm flex-fill"
                onClick={() => handleQuickFill('entrenador')}
              >
                Entrenador
              </button>
              <button
                type="button"
                className="btn btn-outline-secondary btn-sm flex-fill"
                onClick={() => handleQuickFill('estudiante')}
              >
                Estudiante
              </button>
            </div>
          </section>
        </div>

        <div className="card-footer bg-light text-center py-3">
          <small className="text-muted">
            Acceso protegido mediante <strong>Argon2id</strong> y bloqueo contra fuerza bruta.
          </small>
        </div>
      </div>

      {/* Modal de cambio de clave temporal */}
      {showChangePassModal && (
        <div className="modal fade show d-block" tabIndex="-1" role="dialog" style={{ backgroundColor: 'rgba(0,0,0,0.7)' }}>
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content">
              <div className="modal-header bg-warning">
                <h5 className="modal-title fw-bold">Actualización Obligatoria de Contraseña</h5>
              </div>
              <div className="modal-body">
                <p className="small text-muted">
                  Por políticas de ciberseguridad (ISO 27002 / Ley 21.459), debe reemplazar su contraseña temporal por una nueva.
                </p>
                {passChangeError && <div className="alert alert-danger py-2 small">{passChangeError}</div>}
                <form onSubmit={handleUpdatePassword}>
                  <div className="mb-3">
                    <label htmlFor="nueva-clave" className="form-label small fw-semibold">Nueva Contraseña</label>
                    <input
                      type="password"
                      id="nueva-clave"
                      className="form-control"
                      value={nuevaClave}
                      onChange={(e) => setNuevaClave(e.target.value)}
                      placeholder="Mínimo 10 caracteres, mayúsculas, números y símbolos"
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label htmlFor="confirmar-clave" className="form-label small fw-semibold">Confirmar Contraseña</label>
                    <input
                      type="password"
                      id="confirmar-clave"
                      className="form-control"
                      value={confirmarClave}
                      onChange={(e) => setConfirmarClave(e.target.value)}
                      placeholder="Repita la contraseña"
                      required
                    />
                  </div>
                  <button type="submit" className="btn btn-primary w-100">Guardar y Continuar</button>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

export default Login;
