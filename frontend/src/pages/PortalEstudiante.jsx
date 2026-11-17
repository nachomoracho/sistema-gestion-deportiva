import React, { useState, useEffect } from 'react';
import { deportesService } from '../services/deportesService';
import AlertMessage from '../components/AlertMessage';
import { formatearFecha, formatearHora, formatearNota, getEstadoAsistenciaBadge } from '../utils/formatters';

const PortalEstudiante = () => {
  const [datos, setDatos] = useState(null);
  const [notificaciones, setNotificaciones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    cargarPortal();
  }, []);

  const cargarPortal = async () => {
    setLoading(true);
    try {
      const [portalData, notifs] = await Promise.all([
        deportesService.getPortalEstudiante(),
        deportesService.getMisNotificaciones(),
      ]);
      setDatos(portalData);
      setNotificaciones(notifs);
    } catch (err) {
      setErrorMsg(err.message || 'Error al cargar el portal estudiantil.');
    } finally {
      setLoading(false);
    }
  };

  const handleMarcarLeida = async (idNotif) => {
    try {
      await deportesService.marcarNotificacionLeida(idNotif);
      setNotificaciones((prev) =>
        prev.map((n) => (n.id_notificacion === idNotif ? { ...n, leida: true } : n))
      );
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleMarcarTodasLeidas = async () => {
    try {
      await deportesService.marcarTodasNotificacionesLeidas();
      setNotificaciones((prev) => prev.map((n) => ({ ...n, leida: true })));
      setSuccessMsg('Todas las notificaciones han sido marcadas como leídas.');
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  if (loading) {
    return (
      <main className="container text-center py-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Cargando portal...</span>
        </div>
        <p className="mt-2 text-muted">Cargando su información académica deportiva...</p>
      </main>
    );
  }

  const metricas = datos?.metricas || {};
  const estadoBadge = getEstadoAsistenciaBadge(metricas.porcentaje_asistencia || 0);

  return (
    <main className="container py-4">
      {/* Cabecera del Estudiante */}
      <section className="card shadow-sm border-0 mb-4 bg-primary text-white">
        <div className="card-body p-4 d-flex flex-wrap justify-content-between align-items-center gap-3">
          <div>
            <span className="badge bg-light text-primary px-3 py-1 mb-2 fw-bold">Portal del Estudiante</span>
            <h1 className="h3 fw-bold mb-1">{datos?.estudiante?.nombre_completo}</h1>
            <p className="mb-0 opacity-75">
              RUT: {datos?.estudiante?.rut} &bull; Matrícula: {datos?.estudiante?.matricula} &bull; {datos?.estudiante?.correo}
            </p>
          </div>
          <div className="text-end">
            <span className="badge bg-warning text-dark px-3 py-2 fs-6">
              {datos?.disciplinas?.length || 0} Taller(es) Inscrito(s)
            </span>
          </div>
        </div>
      </section>

      <AlertMessage message={errorMsg} variant="danger" onClose={() => setErrorMsg('')} />
      <AlertMessage message={successMsg} variant="success" onClose={() => setSuccessMsg('')} />

      {/* Alerta Preventiva de Inasistencia (CU06 / RNF01) */}
      {metricas.alerta_riesgo && (
        <div className="alert alert-danger d-flex align-items-center shadow-sm mb-4" role="alert">
          <div className="flex-grow-1">
            <h2 className="h6 fw-bold mb-1">¡Alerta Académica: Riesgo de Reprobación por Inasistencia!</h2>
            <p className="mb-0 small">
              Su asistencia acumulada es de <strong>{metricas.porcentaje_asistencia}%</strong>, inferior al mínimo reglamentario exigido del <strong>75%</strong>. Le recomendamos asistir a las próximas sesiones para regularizar su situación.
            </p>
          </div>
        </div>
      )}

      {/* Tarjetas de Métricas de Rendimiento (CU06 / CU07) */}
      <section className="row g-3 mb-4" aria-label="Métricas de rendimiento y asistencia">
        <div className="col-12 col-md-4">
          <article className="card shadow-sm border-0 h-100">
            <div className="card-body text-center p-4">
              <span className="text-muted small fw-bold text-uppercase">Asistencia Acumulada</span>
              <div className="display-5 fw-bold my-2 text-dark">{metricas.porcentaje_asistencia}%</div>
              <span className={estadoBadge.clase}>{estadoBadge.texto}</span>
              <div className="text-muted small mt-2">
                {metricas.total_presente} presentes de {metricas.total_sesiones} sesiones
              </div>
            </div>
          </article>
        </div>

        <div className="col-12 col-md-4">
          <article className="card shadow-sm border-0 h-100">
            <div className="card-body text-center p-4">
              <span className="text-muted small fw-bold text-uppercase">Promedio de Rendimiento</span>
              <div className="display-5 fw-bold my-2 text-primary">{metricas.promedio_rendimiento}</div>
              <span className="badge bg-info text-dark">Escala Oficial 1.0 - 7.0</span>
              <div className="text-muted small mt-2">Evaluación física, táctica y actitudinal</div>
            </div>
          </article>
        </div>

        <div className="col-12 col-md-4">
          <article className="card shadow-sm border-0 h-100">
            <div className="card-body text-center p-4">
              <span className="text-muted small fw-bold text-uppercase">Bandeja de Avisos</span>
              <div className="display-5 fw-bold my-2 text-secondary">
                {notificaciones.filter((n) => !n.leida).length}
              </div>
              <span className="badge bg-secondary">Avisos automáticos (Observer)</span>
              <div className="text-muted small mt-2">Notificaciones directas del docente</div>
            </div>
          </article>
        </div>
      </section>

      {/* Contenedor en 2 columnas: Historial y Notificaciones */}
      <div className="row g-4">
        {/* Columna Izquierda: Historial de Asistencia y Próximas Sesiones */}
        <section className="col-lg-8" aria-labelledby="historial-heading">
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-header bg-white py-3">
              <h2 className="h5 fw-bold mb-0 text-dark" id="historial-heading">
                Historial de Evaluaciones y Asistencias (CU06 / CU07)
              </h2>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover align-middle mb-0">
                  <thead className="table-light">
                    <tr>
                      <th scope="col">Disciplina</th>
                      <th scope="col">Fecha</th>
                      <th scope="col">Asistencia</th>
                      <th scope="col">Nota Rendimiento</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datos?.historial_asistencia?.map((h) => (
                      <tr key={h.id_asistencia}>
                        <td className="fw-semibold">{h.disciplina}</td>
                        <td>{formatearFecha(h.fecha)}</td>
                        <td>
                          {h.estado_presente ? (
                            <span className="badge bg-success">PRESENTE</span>
                          ) : (
                            <span className="badge bg-danger">AUSENTE</span>
                          )}
                        </td>
                        <td className="fw-bold text-primary">
                          {formatearNota(h.puntaje)}
                        </td>
                      </tr>
                    ))}
                    {(!datos?.historial_asistencia || datos.historial_asistencia.length === 0) && (
                      <tr>
                        <td colSpan="4" className="text-center py-4 text-muted">
                          Aún no registra asistencias evaluadas en el sistema.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Próximas Sesiones Programadas */}
          <div className="card shadow-sm border-0">
            <div className="card-header bg-white py-3">
              <h2 className="h5 fw-bold mb-0 text-dark">Próximas Sesiones Programadas</h2>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-striped align-middle mb-0">
                  <thead className="table-light">
                    <tr>
                      <th scope="col">Disciplina</th>
                      <th scope="col">Fecha</th>
                      <th scope="col">Horario</th>
                      <th scope="col">Lugar</th>
                      <th scope="col">Entrenador</th>
                    </tr>
                  </thead>
                  <tbody>
                    {datos?.proximas_sesiones?.map((s) => (
                      <tr key={s.id_sesion}>
                        <td className="fw-semibold">{s.disciplina}</td>
                        <td>{formatearFecha(s.fecha)}</td>
                        <td>{formatearHora(s.hora_inicio)} hrs</td>
                        <td>{s.lugar}</td>
                        <td>{s.entrenador}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        {/* Columna Derecha: Bandeja de Notificaciones (CU08 / Observer) */}
        <aside className="col-lg-4" aria-labelledby="notificaciones-heading">
          <div className="card shadow-sm border-0">
            <div className="card-header bg-white py-3 d-flex justify-content-between align-items-center">
              <h2 className="h6 fw-bold mb-0 text-dark" id="notificaciones-heading">
                Notificaciones (Observer CU08)
              </h2>
              {notificaciones.some((n) => !n.leida) && (
                <button
                  type="button"
                  className="btn btn-outline-primary btn-sm"
                  onClick={handleMarcarTodasLeidas}
                >
                  Marcar todas
                </button>
              )}
            </div>
            <div className="card-body p-2" style={{ maxHeight: '500px', overflowY: 'auto' }}>
              {notificaciones.map((n) => (
                <article
                  key={n.id_notificacion}
                  className={`p-3 rounded mb-2 border ${n.leida ? 'bg-white opacity-75' : 'bg-light border-primary'}`}
                >
                  <div className="d-flex justify-content-between align-items-start mb-1">
                    <span className={`badge ${n.leida ? 'bg-secondary' : 'bg-primary'}`}>
                      {n.leida ? 'Leída' : 'Nueva'}
                    </span>
                    <small className="text-muted" style={{ fontSize: '0.75rem' }}>
                      {new Date(n.fecha_creacion).toLocaleDateString()}
                    </small>
                  </div>
                  <p className="small mb-2 text-dark">{n.mensaje}</p>
                  {!n.leida && (
                    <button
                      type="button"
                      className="btn btn-link btn-sm p-0 text-decoration-none"
                      onClick={() => handleMarcarLeida(n.id_notificacion)}
                    >
                      Marcar como leída
                    </button>
                  )}
                </article>
              ))}

              {notificaciones.length === 0 && (
                <p className="text-center text-muted small py-4 mb-0">
                  No posee notificaciones recientes.
                </p>
              )}
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
};

export default PortalEstudiante;
