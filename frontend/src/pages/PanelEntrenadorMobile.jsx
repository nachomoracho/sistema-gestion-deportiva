import React, { useState, useEffect } from 'react';
import { deportesService } from '../services/deportesService';
import AlertMessage from '../components/AlertMessage';
import { formatearFecha, formatearHora } from '../utils/formatters';

const PanelEntrenadorMobile = () => {
  const [sesiones, setSesiones] = useState([]);
  const [sesionSeleccionada, setSesionSeleccionada] = useState(null);
  const [estudiantes, setEstudiantes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  useEffect(() => {
    cargarSesiones();
  }, []);

  const cargarSesiones = async () => {
    setLoading(true);
    try {
      const data = await deportesService.getSesiones();
      setSesiones(data);
      if (data.length > 0) {
        seleccionarSesion(data[0].id_sesion);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Error al cargar sesiones.');
    } finally {
      setLoading(false);
    }
  };

  const seleccionarSesion = async (idSesion) => {
    setLoading(true);
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const data = await deportesService.getNominaSesion(idSesion);
      setSesionSeleccionada(data.sesion);
      
      // Inicializar nómina con estados existentes o por defecto
      const lista = data.estudiantes.map((est) => ({
        ...est,
        estado_presente: est.estado_presente !== undefined ? est.estado_presente : false,
        puntaje: est.puntaje !== null && est.puntaje !== undefined ? est.puntaje.toString() : '5.0',
      }));
      setEstudiantes(lista);
    } catch (err) {
      setErrorMsg(err.message || 'Error al obtener nómina de la sesión.');
    } finally {
      setLoading(false);
    }
  };

  const toggleAsistencia = (rut) => {
    setEstudiantes((prev) =>
      prev.map((item) =>
        item.rut === rut ? { ...item, estado_presente: !item.estado_presente } : item
      )
    );
  };

  const handlePuntajeChange = (rut, val) => {
    setEstudiantes((prev) =>
      prev.map((item) =>
        item.rut === rut ? { ...item, puntaje: val } : item
      )
    );
  };

  const handleGuardarTodo = async () => {
    if (!sesionSeleccionada) return;
    setSaving(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const payload = estudiantes.map((e) => ({
        rut_estudiante: e.rut,
        estado_presente: e.estado_presente,
        puntaje: e.estado_presente && e.puntaje ? parseFloat(e.puntaje) : null,
      }));

      const res = await deportesService.bulkGuardarAsistencia(sesionSeleccionada.id_sesion, payload);
      setSuccessMsg(res.mensaje || 'Asistencias y evaluaciones registradas con éxito (Observer notificado).');
    } catch (err) {
      setErrorMsg(err.message || 'Error al registrar asistencias.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <main className="container-fluid py-3 px-2 px-sm-3 px-md-4" style={{ maxWidth: '960px' }}>
      {/* Encabezado móvil */}
      <section className="mb-3 text-center text-sm-start">
        <span className="badge bg-success mb-1">Módulo de Campo</span>
        <h1 className="h3 fw-bold mb-1">Control de Asistencia en Cancha</h1>
        <p className="text-muted small mb-2">
          Diseñado para operación táctil rápida en terreno (Mobile-First 360 px)
        </p>
      </section>

      <AlertMessage message={errorMsg} variant="danger" onClose={() => setErrorMsg('')} />
      <AlertMessage message={successMsg} variant="success" onClose={() => setSuccessMsg('')} />

      {/* Selector de Sesión */}
      <section className="card shadow-sm border-0 mb-3" aria-labelledby="label-sesion-activa">
        <div className="card-body p-3">
          <label htmlFor="select-sesion" id="label-sesion-activa" className="form-label fw-bold small text-uppercase text-secondary">
            Seleccionar Sesión de Entrenamiento:
          </label>
          <select
            id="select-sesion"
            className="form-select form-select-lg fw-semibold"
            value={sesionSeleccionada?.id_sesion || ''}
            onChange={(e) => seleccionarSesion(e.target.value)}
            disabled={loading || saving}
          >
            {sesiones.map((s) => (
              <option key={s.id_sesion} value={s.id_sesion}>
                {s.disciplina_nombre} — {formatearFecha(s.fecha)} ({formatearHora(s.hora_inicio)}) en {s.lugar}
              </option>
            ))}
          </select>
        </div>
      </section>

      {/* Detalle de sesión seleccionada */}
      {sesionSeleccionada && (
        <article className="card shadow-sm border-0 mb-3 bg-light">
          <div className="card-body p-3 d-flex flex-wrap justify-content-between align-items-center gap-2">
            <div>
              <h2 className="h5 fw-bold text-dark mb-0">{sesionSeleccionada.disciplina_nombre}</h2>
              <small className="text-muted">
                {formatearFecha(sesionSeleccionada.fecha)} &bull; {formatearHora(sesionSeleccionada.hora_inicio)} hrs &bull; {sesionSeleccionada.lugar}
              </small>
            </div>
            <div className="badge bg-primary fs-6 px-3 py-2">
              {estudiantes.length} Alumnos en Nómina
            </div>
          </div>
        </article>
      )}

      {/* Nómina de Alumnos en Tarjetas Táctiles */}
      <section aria-label="Nómina de estudiantes">
        {estudiantes.map((est) => (
          <article
            key={est.rut}
            className={`card shadow-sm border-0 mb-3 transition-card ${
              est.estado_presente ? 'border-start border-success border-4' : 'border-start border-secondary border-4'
            }`}
          >
            <div className="card-body p-3">
              <div className="d-flex justify-content-between align-items-start mb-2">
                <div>
                  <h3 className="h6 fw-bold mb-0 text-dark">{est.nombre_completo}</h3>
                  <div className="text-muted small">
                    RUT: {est.rut} &bull; Matrícula: {est.matricula || 'N/A'}
                  </div>
                </div>
                <span className={`badge ${est.estado_presente ? 'bg-success' : 'bg-secondary'}`}>
                  {est.estado_presente ? 'PRESENTE' : 'AUSENTE'}
                </span>
              </div>

              <div className="row g-2 align-items-center mt-1">
                {/* Botón táctil grande para marcar asistencia */}
                <div className="col-7 col-sm-8">
                  <button
                    type="button"
                    className={`btn w-100 py-2 fw-bold d-flex align-items-center justify-content-center gap-2 shadow-sm ${
                      est.estado_presente ? 'btn-success' : 'btn-outline-secondary'
                    }`}
                    onClick={() => toggleAsistencia(est.rut)}
                    aria-label={`Marcar asistencia para ${est.nombre_completo}`}
                  >
                    <span>{est.estado_presente ? '✓ Asistencia Marcada' : '○ Marcar Presente'}</span>
                  </button>
                </div>

                {/* Calificación de Rendimiento */}
                <div className="col-5 col-sm-4">
                  <label htmlFor={`nota-${est.rut}`} className="form-label visually-hidden">
                    Nota de rendimiento para {est.nombre_completo}
                  </label>
                  <div className="input-group">
                    <span className="input-group-text small bg-white text-muted">Nota</span>
                    <input
                      type="number"
                      step="0.1"
                      min="1.0"
                      max="7.0"
                      id={`nota-${est.rut}`}
                      className="form-control text-center fw-bold"
                      value={est.puntaje}
                      disabled={!est.estado_presente}
                      onChange={(e) => handlePuntajeChange(est.rut, e.target.value)}
                      placeholder="1.0-7.0"
                    />
                  </div>
                </div>
              </div>
            </div>
          </article>
        ))}

        {estudiantes.length === 0 && !loading && (
          <div className="alert alert-info text-center py-4">
            No existen alumnos inscritos formalmente en esta disciplina deportiva.
          </div>
        )}
      </section>

      {/* Botón flotante / barra fija inferior de guardado */}
      {estudiantes.length > 0 && (
        <aside className="sticky-bottom bg-white py-3 border-top shadow-lg px-2 text-center" aria-label="Acción de guardado masivo">
          <button
            type="button"
            className="btn btn-primary btn-lg w-100 fw-bold shadow py-3 d-flex align-items-center justify-content-center gap-2"
            disabled={saving}
            onClick={handleGuardarTodo}
            id="btn-guardar-asistencia-bulk"
          >
            {saving ? (
              <>
                <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Guardando y Notificando (Observer)...
              </>
            ) : (
              <>
                <span>Guardar Nómina y Calificaciones</span>
              </>
            )}
          </button>
        </aside>
      )}
    </main>
  );
};

export default PanelEntrenadorMobile;
