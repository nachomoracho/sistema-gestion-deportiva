import React, { useState, useEffect } from 'react';
import { deportesService } from '../services/deportesService';
import AlertMessage from '../components/AlertMessage';
import EnDesarrolloModal from '../components/EnDesarrolloModal';
import { formatearFecha, formatearNota } from '../utils/formatters';

const ReporteriaAvanzada = () => {
  const [reporte, setReporte] = useState(null);
  const [disciplinas, setDisciplinas] = useState([]);
  const [estudiantes, setEstudiantes] = useState([]);
  const [entrenadores, setEntrenadores] = useState([]);

  const [filtros, setFiltros] = useState({
    rut_estudiante: '',
    id_disciplina: '',
    rut_entrenador: '',
  });

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [showPdfModal, setShowPdfModal] = useState(false);

  useEffect(() => {
    cargarCatalogos();
    cargarReporte({});
  }, []);

  const cargarCatalogos = async () => {
    try {
      const [d, est, ent] = await Promise.all([
        deportesService.getDisciplinas(),
        deportesService.getUsuarios({ perfil: 'ESTUDIANTE' }),
        deportesService.getUsuarios({ perfil: 'ENTRENADOR' }),
      ]);
      setDisciplinas(d);
      setEstudiantes(est);
      setEntrenadores(ent);
    } catch {
      // Ignorar error no crítico
    }
  };

  const cargarReporte = async (params) => {
    setLoading(true);
    setErrorMsg('');
    try {
      const data = await deportesService.getReportes(params);
      setReporte(data);
    } catch (err) {
      setErrorMsg(err.message || 'Error al generar reporte analítico.');
    } finally {
      setLoading(false);
    }
  };

  const handleFiltrar = (e) => {
    e.preventDefault();
    cargarReporte(filtros);
  };

  const handleLimpiarFiltros = () => {
    const f = { rut_estudiante: '', id_disciplina: '', rut_entrenador: '' };
    setFiltros(f);
    cargarReporte(f);
  };

  const handleExportarCsv = () => {
    const params = new URLSearchParams();
    if (filtros.rut_estudiante) params.set('rut_estudiante', filtros.rut_estudiante);
    if (filtros.id_disciplina) params.set('id_disciplina', filtros.id_disciplina);
    if (filtros.rut_entrenador) params.set('rut_entrenador', filtros.rut_entrenador);
    params.set('export', 'csv');

    const token = sessionStorage.getItem('token');
    const url = `http://localhost:8000/api/reportes/?${params.toString()}`;

    // Descarga segura mediante fetch con token Bearer
    fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Error al generar archivo CSV.');
        return res.blob();
      })
      .then((blob) => {
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = `reporte_sgad_${new Date().toISOString().slice(0, 10)}.csv`;
        link.click();
      })
      .catch((err) => setErrorMsg(err.message));
  };

  const resumen = reporte?.resumen || {};
  const registros = reporte?.registros || [];

  return (
    <main className="container-fluid py-4 px-lg-5">
      {/* Encabezado */}
      <section className="d-flex flex-wrap justify-content-between align-items-center mb-4 border-bottom pb-3 gap-2">
        <div>
          <span className="badge bg-secondary mb-1">Módulo Estratégico</span>
          <h1 className="h2 fw-bold text-dark mb-1">Reportería y Analítica Avanzada (RF05)</h1>
          <p className="text-muted mb-0">Métricas consolidadas, análisis de asistencia y rendimiento deportivo</p>
        </div>

        <div className="d-flex gap-2">
          <button
            type="button"
            className="btn btn-outline-danger d-flex align-items-center gap-1 shadow-sm"
            onClick={() => setShowPdfModal(true)}
            aria-label="Exportar a PDF institucional"
          >
            <span>Exportar PDF</span>
          </button>
          <button
            type="button"
            className="btn btn-success d-flex align-items-center gap-1 shadow-sm"
            onClick={handleExportarCsv}
            id="btn-exportar-csv"
            aria-label="Descargar reporte en formato CSV compatible con Excel"
          >
            <span>Descargar CSV Oficial</span>
          </button>
        </div>
      </section>

      <AlertMessage message={errorMsg} variant="danger" onClose={() => setErrorMsg('')} />

      {/* Formulario de Filtros Cruzados Dinámicos (RF05) */}
      <section className="card shadow-sm border-0 mb-4" aria-labelledby="heading-filtros">
        <div className="card-header bg-white py-3">
          <h2 className="h6 fw-bold mb-0 text-dark" id="heading-filtros">Filtros Cruzados Dinámicos</h2>
        </div>
        <div className="card-body p-3">
          <form onSubmit={handleFiltrar} className="row g-3">
            <div className="col-12 col-md-4">
              <label htmlFor="filtro-estudiante" className="form-label small fw-semibold">Estudiante</label>
              <select
                id="filtro-estudiante"
                className="form-select"
                value={filtros.rut_estudiante}
                onChange={(e) => setFiltros({ ...filtros, rut_estudiante: e.target.value })}
              >
                <option value="">-- Todos los estudiantes --</option>
                {estudiantes.map((est) => (
                  <option key={est.rut} value={est.rut}>
                    {est.nombre} {est.apellido} ({est.rut})
                  </option>
                ))}
              </select>
            </div>

            <div className="col-12 col-md-4">
              <label htmlFor="filtro-disciplina" className="form-label small fw-semibold">Disciplina Deportiva</label>
              <select
                id="filtro-disciplina"
                className="form-select"
                value={filtros.id_disciplina}
                onChange={(e) => setFiltros({ ...filtros, id_disciplina: e.target.value })}
              >
                <option value="">-- Todas las disciplinas --</option>
                {disciplinas.map((d) => (
                  <option key={d.id_disciplina} value={d.id_disciplina}>{d.nombre}</option>
                ))}
              </select>
            </div>

            <div className="col-12 col-md-4">
              <label htmlFor="filtro-entrenador" className="form-label small fw-semibold">Entrenador a Cargo</label>
              <select
                id="filtro-entrenador"
                className="form-select"
                value={filtros.rut_entrenador}
                onChange={(e) => setFiltros({ ...filtros, rut_entrenador: e.target.value })}
              >
                <option value="">-- Todos los entrenadores --</option>
                {entrenadores.map((ent) => (
                  <option key={ent.rut} value={ent.rut}>
                    {ent.nombre} {ent.apellido} ({ent.especialidad})
                  </option>
                ))}
              </select>
            </div>

            <div className="col-12 d-flex justify-content-end gap-2 mt-3">
              <button
                type="button"
                className="btn btn-outline-secondary btn-sm px-3"
                onClick={handleLimpiarFiltros}
              >
                Limpiar Filtros
              </button>
              <button
                type="submit"
                className="btn btn-primary btn-sm px-4 fw-bold shadow-sm"
                disabled={loading}
              >
                {loading ? 'Consultando...' : 'Aplicar Filtros'}
              </button>
            </div>
          </form>
        </div>
      </section>

      {/* Tarjetas de Métricas Agregadas */}
      <section className="row g-3 mb-4" aria-label="Resumen estadístico">
        <div className="col-6 col-md-3">
          <article className="card shadow-sm border-0 text-center p-3">
            <span className="text-muted small fw-bold">TOTAL REGISTROS</span>
            <div className="display-6 fw-bold text-dark my-1">{resumen.total_registros ?? 0}</div>
            <small className="text-muted">Evaluaciones computadas</small>
          </article>
        </div>

        <div className="col-6 col-md-3">
          <article className="card shadow-sm border-0 text-center p-3">
            <span className="text-muted small fw-bold">ASISTENCIA GLOBAL</span>
            <div className="display-6 fw-bold text-success my-1">{resumen.porcentaje_asistencia ?? 0}%</div>
            <small className="text-muted">{resumen.total_presentes ?? 0} asistencias efectivas</small>
          </article>
        </div>

        <div className="col-6 col-md-3">
          <article className="card shadow-sm border-0 text-center p-3">
            <span className="text-muted small fw-bold">TOTAL AUSENCIAS</span>
            <div className="display-6 fw-bold text-danger my-1">{resumen.total_ausentes ?? 0}</div>
            <small className="text-muted">Inasistencias registradas</small>
          </article>
        </div>

        <div className="col-6 col-md-3">
          <article className="card shadow-sm border-0 text-center p-3">
            <span className="text-muted small fw-bold">PROMEDIO RENDIMIENTO</span>
            <div className="display-6 fw-bold text-primary my-1">{resumen.promedio_puntaje ?? 0}</div>
            <small className="text-muted">Escala académica 1.0 - 7.0</small>
          </article>
        </div>
      </section>

      {/* Tabla Detallada Responsiva */}
      <section className="card shadow-sm border-0" aria-labelledby="tabla-reporte-heading">
        <div className="card-header bg-white py-3">
          <h2 className="h5 fw-bold mb-0 text-dark" id="tabla-reporte-heading">
            Detalle Consolidado de Asistencias y Calificaciones
          </h2>
        </div>
        <div className="card-body p-0">
          <div className="table-responsive">
            <table className="table table-hover table-striped align-middle mb-0">
              <thead className="table-dark">
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Estudiante</th>
                  <th scope="col">RUT</th>
                  <th scope="col">Disciplina</th>
                  <th scope="col">Fecha</th>
                  <th scope="col">Entrenador</th>
                  <th scope="col">Estado</th>
                  <th scope="col">Nota Rendimiento</th>
                </tr>
              </thead>
              <tbody>
                {registros.map((r) => (
                  <tr key={r.id_asistencia}>
                    <td>{r.id_asistencia}</td>
                    <td className="fw-semibold">{r.estudiante_nombre}</td>
                    <td>{r.rut_estudiante}</td>
                    <td><span className="badge bg-secondary">{r.disciplina}</span></td>
                    <td>{formatearFecha(r.fecha)}</td>
                    <td>{r.entrenador}</td>
                    <td>
                      {r.estado_presente ? (
                        <span className="badge bg-success">PRESENTE</span>
                      ) : (
                        <span className="badge bg-danger">AUSENTE</span>
                      )}
                    </td>
                    <td className="fw-bold text-primary">{formatearNota(r.puntaje)}</td>
                  </tr>
                ))}
                {registros.length === 0 && (
                  <tr>
                    <td colSpan="8" className="text-center py-4 text-muted">
                      No se encontraron registros con los filtros seleccionados.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Modal En Desarrollo para Exportación PDF */}
      <EnDesarrolloModal
        show={showPdfModal}
        onClose={() => setShowPdfModal(false)}
        titulo="Exportación de Dossier en Formato PDF Oficial"
        descripcion="El generador de reportes consolidados en formato PDF vectorial institucional se incorporará en el Sprint 4 con firma electrónica avanzada."
      />
    </main>
  );
};

export default ReporteriaAvanzada;
