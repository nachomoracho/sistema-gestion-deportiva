import React, { useState, useEffect } from 'react';
import { deportesService } from '../services/deportesService';
import AlertMessage from '../components/AlertMessage';
import EnDesarrolloModal from '../components/EnDesarrolloModal';
import { formatearFecha, formatearHora } from '../utils/formatters';

const DashboardCoordinador = () => {
  const [activeTab, setActiveTab] = useState('disciplinas');
  const [disciplinas, setDisciplinas] = useState([]);
  const [estudiantes, setEstudiantes] = useState([]);
  const [entrenadores, setEntrenadores] = useState([]);
  const [sesiones, setSesiones] = useState([]);
  const [inscripciones, setInscripciones] = useState([]);

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Modales
  const [showModalDisciplina, setShowModalDisciplina] = useState(false);
  const [showModalInscripcion, setShowModalInscripcion] = useState(false);
  const [showModalSesion, setShowModalSesion] = useState(false);
  const [showModalUsuario, setShowModalUsuario] = useState(false);
  const [showAdapterModal, setShowAdapterModal] = useState(false);
  const [adapterPayload, setAdapterPayload] = useState(null);

  // Form states
  const [formDisc, setFormDisc] = useState({ nombre: '', cupo_maximo: 20 });
  const [formInsc, setFormInsc] = useState({ rut_estudiante: '', id_disciplina: '' });
  const [formSes, setFormSes] = useState({
    fecha: '',
    hora_inicio: '10:00',
    lugar: '',
    id_disciplina: '',
    rut_entrenador: '',
  });
  const [formUser, setFormUser] = useState({
    perfil: 'ENTRENADOR',
    rut: '',
    nombre: '',
    apellido: '',
    correo: '',
    clave: 'Segura2026!#Temp',
    especialidad: '',
    matricula: '',
  });

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      const [d, est, ent, s, i] = await Promise.all([
        deportesService.getDisciplinas(),
        deportesService.getUsuarios({ perfil: 'ESTUDIANTE' }),
        deportesService.getUsuarios({ perfil: 'ENTRENADOR' }),
        deportesService.getSesiones(),
        deportesService.getInscripciones(),
      ]);
      setDisciplinas(d);
      setEstudiantes(est);
      setEntrenadores(ent);
      setSesiones(s);
      setInscripciones(i);
    } catch (err) {
      setErrorMsg(err.message || 'Error al cargar datos del panel.');
    } finally {
      setLoading(false);
    }
  };

  // Crear Disciplina
  const handleCrearDisciplina = async (e) => {
    e.preventDefault();
    try {
      await deportesService.createDisciplina(formDisc);
      setSuccessMsg(`Disciplina '${formDisc.nombre}' creada exitosamente.`);
      setShowModalDisciplina(false);
      setFormDisc({ nombre: '', cupo_maximo: 20 });
      cargarDatos();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  // Inscribir Estudiante
  const handleCrearInscripcion = async (e) => {
    e.preventDefault();
    try {
      await deportesService.createInscripcion({
        rut_estudiante: formInsc.rut_estudiante,
        id_disciplina: parseInt(formInsc.id_disciplina, 10),
      });
      setSuccessMsg('Estudiante inscrito exitosamente con validación de cupos.');
      setShowModalInscripcion(false);
      setFormInsc({ rut_estudiante: '', id_disciplina: '' });
      cargarDatos();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  // Programar Sesión
  const handleCrearSesion = async (e) => {
    e.preventDefault();
    try {
      await deportesService.createSesion({
        ...formSes,
        id_disciplina: parseInt(formSes.id_disciplina, 10),
      });
      setSuccessMsg('Sesión programada con éxito.');
      setShowModalSesion(false);
      cargarDatos();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  // Crear Usuario (Factory)
  const handleCrearUsuario = async (e) => {
    e.preventDefault();
    try {
      await deportesService.createUsuario({
        id_perfil: formUser.perfil === 'ENTRENADOR' ? 2 : 3,
        rut: formUser.rut,
        nombre: formUser.nombre,
        apellido: formUser.apellido,
        correo: formUser.correo,
        clave: formUser.clave,
        especialidad: formUser.perfil === 'ENTRENADOR' ? formUser.especialidad : null,
        matricula: formUser.perfil === 'ESTUDIANTE' ? formUser.matricula : null,
      });
      setSuccessMsg(`Usuario ${formUser.nombre} ${formUser.apellido} registrado exitosamente vía Factory.`);
      setShowModalUsuario(false);
      cargarDatos();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  // Disparar sincronización Adapter
  const handleTriggerAdapter = async () => {
    try {
      const res = await deportesService.sincronizarIntranetAdapter();
      setAdapterPayload(res.payload_interoperable);
      setShowAdapterModal(true);
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  return (
    <main className="container-fluid py-4 px-lg-5">
      <section className="d-flex flex-wrap justify-content-between align-items-center mb-4 border-bottom pb-3 gap-2">
        <div>
          <h1 className="h2 mb-1 fw-bold text-dark">Panel de Control del Coordinador</h1>
          <p className="text-muted mb-0">Gestión de disciplinas, cupos transaccionales y nóminas</p>
        </div>

        <div className="d-flex gap-2">
          <button
            type="button"
            className="btn btn-outline-primary d-flex align-items-center gap-1 shadow-sm"
            onClick={handleTriggerAdapter}
            aria-label="Sincronizar con Intranet Académica"
          >
            <span>Sincronizar Intranet (Adapter)</span>
          </button>
        </div>
      </section>

      <AlertMessage message={errorMsg} variant="danger" onClose={() => setErrorMsg('')} />
      <AlertMessage message={successMsg} variant="success" onClose={() => setSuccessMsg('')} />

      {/* Navegación por pestañas */}
      <nav aria-label="Secciones del panel de coordinador">
        <ul className="nav nav-pills mb-4 gap-2" role="tablist">
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === 'disciplinas' ? 'active' : 'bg-white text-dark border'}`}
              onClick={() => setActiveTab('disciplinas')}
            >
              Disciplinas ({disciplinas.length})
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === 'inscripciones' ? 'active' : 'bg-white text-dark border'}`}
              onClick={() => setActiveTab('inscripciones')}
            >
              Inscripciones ({inscripciones.length})
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === 'sesiones' ? 'active' : 'bg-white text-dark border'}`}
              onClick={() => setActiveTab('sesiones')}
            >
              Sesiones ({sesiones.length})
            </button>
          </li>
          <li className="nav-item">
            <button
              className={`nav-link ${activeTab === 'usuarios' ? 'active' : 'bg-white text-dark border'}`}
              onClick={() => setActiveTab('usuarios')}
            >
              Usuarios (Entrenadores y Alumnos)
            </button>
          </li>
        </ul>
      </nav>

      {/* TAB 1: DISCIPLINAS */}
      {activeTab === 'disciplinas' && (
        <section aria-labelledby="heading-disciplinas">
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-header bg-white py-3 d-flex justify-content-between align-items-center">
              <h2 className="h5 mb-0 fw-bold" id="heading-disciplinas">Catálogo Oficial de Disciplinas Deportivas</h2>
              <button
                type="button"
                className="btn btn-success btn-sm px-3"
                onClick={() => setShowModalDisciplina(true)}
              >
                + Nueva Disciplina
              </button>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover table-striped align-middle mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th scope="col">ID</th>
                      <th scope="col">Disciplina</th>
                      <th scope="col">Cupo Máximo</th>
                      <th scope="col">Inscritos</th>
                      <th scope="col">Disponibles</th>
                      <th scope="col">Estado de Capacidad</th>
                    </tr>
                  </thead>
                  <tbody>
                    {disciplinas.map((d) => (
                      <tr key={d.id_disciplina}>
                        <td className="fw-semibold">{d.id_disciplina}</td>
                        <td className="fw-bold">{d.nombre}</td>
                        <td>{d.cupo_maximo}</td>
                        <td>{d.cupos_ocupados}</td>
                        <td>{d.cupos_disponibles}</td>
                        <td>
                          {d.cupos_disponibles === 0 ? (
                            <span className="badge bg-danger">Agotado</span>
                          ) : d.cupos_disponibles <= 5 ? (
                            <span className="badge bg-warning text-dark">Últimos cupos</span>
                          ) : (
                            <span className="badge bg-success">Disponible</span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {disciplinas.length === 0 && (
                      <tr>
                        <td colSpan="6" className="text-center py-4 text-muted">
                          No existen disciplinas registradas.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* TAB 2: INSCRIPCIONES */}
      {activeTab === 'inscripciones' && (
        <section aria-labelledby="heading-inscripciones">
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-header bg-white py-3 d-flex justify-content-between align-items-center">
              <h2 className="h5 mb-0 fw-bold" id="heading-inscripciones">Inscripción Formal de Alumnos (Control de Cupos)</h2>
              <button
                type="button"
                className="btn btn-primary btn-sm px-3"
                onClick={() => setShowModalInscripcion(true)}
              >
                + Inscribir Estudiante
              </button>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover table-striped align-middle mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th scope="col">ID</th>
                      <th scope="col">Estudiante</th>
                      <th scope="col">RUT</th>
                      <th scope="col">Matrícula</th>
                      <th scope="col">Disciplina</th>
                      <th scope="col">Fecha Inscripción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {inscripciones.map((i) => (
                      <tr key={i.id_inscripcion}>
                        <td>{i.id_inscripcion}</td>
                        <td className="fw-bold">{i.estudiante_detalle?.nombre_completo}</td>
                        <td>{i.estudiante_detalle?.rut}</td>
                        <td>{i.estudiante_detalle?.matricula || '-'}</td>
                        <td><span className="badge bg-secondary">{i.disciplina_detalle?.nombre}</span></td>
                        <td>{formatearFecha(i.fecha_inscripcion)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* TAB 3: SESIONES */}
      {activeTab === 'sesiones' && (
        <section aria-labelledby="heading-sesiones">
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-header bg-white py-3 d-flex justify-content-between align-items-center">
              <h2 className="h5 mb-0 fw-bold" id="heading-sesiones">Programación de Clases y Entrenamientos</h2>
              <button
                type="button"
                className="btn btn-success btn-sm px-3"
                onClick={() => setShowModalSesion(true)}
              >
                + Programar Sesión
              </button>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover table-striped align-middle mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th scope="col">ID</th>
                      <th scope="col">Disciplina</th>
                      <th scope="col">Fecha</th>
                      <th scope="col">Hora</th>
                      <th scope="col">Lugar</th>
                      <th scope="col">Entrenador a Cargo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sesiones.map((s) => (
                      <tr key={s.id_sesion}>
                        <td>{s.id_sesion}</td>
                        <td className="fw-bold">{s.disciplina_nombre}</td>
                        <td>{formatearFecha(s.fecha)}</td>
                        <td>{formatearHora(s.hora_inicio)}</td>
                        <td>{s.lugar}</td>
                        <td>{s.entrenador_nombre}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* TAB 4: USUARIOS (FACTORY) */}
      {activeTab === 'usuarios' && (
        <section aria-labelledby="heading-usuarios">
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-header bg-white py-3 d-flex justify-content-between align-items-center">
              <h2 className="h5 mb-0 fw-bold" id="heading-usuarios">Registro de Docentes y Estudiantes (Patrón Factory)</h2>
              <button
                type="button"
                className="btn btn-primary btn-sm px-3"
                onClick={() => setShowModalUsuario(true)}
              >
                + Nuevo Usuario
              </button>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover table-striped align-middle mb-0">
                  <thead className="table-dark">
                    <tr>
                      <th scope="col">RUT</th>
                      <th scope="col">Nombre</th>
                      <th scope="col">Correo</th>
                      <th scope="col">Perfil</th>
                      <th scope="col">Dato Específico</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...entrenadores, ...estudiantes].map((u) => (
                      <tr key={u.rut}>
                        <td className="fw-bold">{u.rut}</td>
                        <td>{u.nombre} {u.apellido}</td>
                        <td>{u.correo}</td>
                        <td>
                          <span className={`badge ${u.perfil_nombre === 'ENTRENADOR' ? 'bg-success' : 'bg-info text-dark'}`}>
                            {u.perfil_nombre}
                          </span>
                        </td>
                        <td>
                          {u.perfil_nombre === 'ENTRENADOR'
                            ? `Esp: ${u.especialidad || 'N/A'}`
                            : `Mat: ${u.matricula || 'N/A'}`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* MODAL NUEVA DISCIPLINA */}
      {showModalDisciplina && (
        <div className="modal fade show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header bg-dark text-white">
                <h5 className="modal-title">Nueva Disciplina Deportiva</h5>
                <button type="button" className="btn-close btn-close-white" onClick={() => setShowModalDisciplina(false)} />
              </div>
              <form onSubmit={handleCrearDisciplina}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label htmlFor="disc-nombre" className="form-label fw-semibold">Nombre de Disciplina</label>
                    <input
                      type="text"
                      id="disc-nombre"
                      className="form-control"
                      value={formDisc.nombre}
                      onChange={(e) => setFormDisc({ ...formDisc, nombre: e.target.value })}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label htmlFor="disc-cupo" className="form-label fw-semibold">Cupo Máximo</label>
                    <input
                      type="number"
                      id="disc-cupo"
                      className="form-control"
                      min="1"
                      max="500"
                      value={formDisc.cupo_maximo}
                      onChange={(e) => setFormDisc({ ...formDisc, cupo_maximo: parseInt(e.target.value, 10) })}
                      required
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowModalDisciplina(false)}>Cancelar</button>
                  <button type="submit" className="btn btn-primary">Guardar Disciplina</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* MODAL NUEVA INSCRIPCIÓN */}
      {showModalInscripcion && (
        <div className="modal fade show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header bg-dark text-white">
                <h5 className="modal-title">Inscribir Alumno en Taller</h5>
                <button type="button" className="btn-close btn-close-white" onClick={() => setShowModalInscripcion(false)} />
              </div>
              <form onSubmit={handleCrearInscripcion}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label htmlFor="insc-estudiante" className="form-label fw-semibold">Seleccionar Estudiante</label>
                    <select
                      id="insc-estudiante"
                      className="form-select"
                      value={formInsc.rut_estudiante}
                      onChange={(e) => setFormInsc({ ...formInsc, rut_estudiante: e.target.value })}
                      required
                    >
                      <option value="">-- Seleccione un estudiante --</option>
                      {estudiantes.map((e) => (
                        <option key={e.rut} value={e.rut}>
                          {e.nombre} {e.apellido} ({e.rut}) - {e.matricula}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-3">
                    <label htmlFor="insc-disciplina" className="form-label fw-semibold">Disciplina</label>
                    <select
                      id="insc-disciplina"
                      className="form-select"
                      value={formInsc.id_disciplina}
                      onChange={(e) => setFormInsc({ ...formInsc, id_disciplina: e.target.value })}
                      required
                    >
                      <option value="">-- Seleccione disciplina --</option>
                      {disciplinas.map((d) => (
                        <option key={d.id_disciplina} value={d.id_disciplina} disabled={d.cupos_disponibles === 0}>
                          {d.nombre} (Disponibles: {d.cupos_disponibles}/{d.cupo_maximo})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowModalInscripcion(false)}>Cancelar</button>
                  <button type="submit" className="btn btn-primary">Confirmar Inscripción</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* MODAL NUEVA SESIÓN */}
      {showModalSesion && (
        <div className="modal fade show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header bg-dark text-white">
                <h5 className="modal-title">Programar Nueva Sesión</h5>
                <button type="button" className="btn-close btn-close-white" onClick={() => setShowModalSesion(false)} />
              </div>
              <form onSubmit={handleCrearSesion}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label htmlFor="ses-disc" className="form-label fw-semibold">Disciplina</label>
                    <select
                      id="ses-disc"
                      className="form-select"
                      value={formSes.id_disciplina}
                      onChange={(e) => setFormSes({ ...formSes, id_disciplina: e.target.value })}
                      required
                    >
                      <option value="">-- Seleccione disciplina --</option>
                      {disciplinas.map((d) => (
                        <option key={d.id_disciplina} value={d.id_disciplina}>{d.nombre}</option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-3">
                    <label htmlFor="ses-coach" className="form-label fw-semibold">Entrenador a Cargo</label>
                    <select
                      id="ses-coach"
                      className="form-select"
                      value={formSes.rut_entrenador}
                      onChange={(e) => setFormSes({ ...formSes, rut_entrenador: e.target.value })}
                      required
                    >
                      <option value="">-- Seleccione entrenador --</option>
                      {entrenadores.map((ent) => (
                        <option key={ent.rut} value={ent.rut}>{ent.nombre} {ent.apellido} ({ent.especialidad})</option>
                      ))}
                    </select>
                  </div>
                  <div className="row g-2 mb-3">
                    <div className="col-md-6">
                      <label htmlFor="ses-fecha" className="form-label fw-semibold">Fecha</label>
                      <input
                        type="date"
                        id="ses-fecha"
                        className="form-control"
                        value={formSes.fecha}
                        onChange={(e) => setFormSes({ ...formSes, fecha: e.target.value })}
                        required
                      />
                    </div>
                    <div className="col-md-6">
                      <label htmlFor="ses-hora" className="form-label fw-semibold">Hora de Inicio</label>
                      <input
                        type="time"
                        id="ses-hora"
                        className="form-control"
                        value={formSes.hora_inicio}
                        onChange={(e) => setFormSes({ ...formSes, hora_inicio: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="mb-3">
                    <label htmlFor="ses-lugar" className="form-label fw-semibold">Lugar / Cancha</label>
                    <input
                      type="text"
                      id="ses-lugar"
                      className="form-control"
                      placeholder="Ej. Cancha Sintética 1"
                      value={formSes.lugar}
                      onChange={(e) => setFormSes({ ...formSes, lugar: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowModalSesion(false)}>Cancelar</button>
                  <button type="submit" className="btn btn-primary">Programar Sesión</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* MODAL NUEVO USUARIO (FACTORY) */}
      {showModalUsuario && (
        <div className="modal fade show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header bg-dark text-white">
                <h5 className="modal-title">Alta de Usuario (UsuarioFactory)</h5>
                <button type="button" className="btn-close btn-close-white" onClick={() => setShowModalUsuario(false)} />
              </div>
              <form onSubmit={handleCrearUsuario}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label htmlFor="user-perfil" className="form-label fw-semibold">Perfil</label>
                    <select
                      id="user-perfil"
                      className="form-select"
                      value={formUser.perfil}
                      onChange={(e) => setFormUser({ ...formUser, perfil: e.target.value })}
                    >
                      <option value="ENTRENADOR">Entrenador (Exige Especialidad)</option>
                      <option value="ESTUDIANTE">Estudiante (Exige Matrícula)</option>
                    </select>
                  </div>
                  <div className="row g-2 mb-3">
                    <div className="col-md-6">
                      <label htmlFor="user-rut" className="form-label fw-semibold">RUT (Módulo 11)</label>
                      <input
                        type="text"
                        id="user-rut"
                        className="form-control"
                        placeholder="12345678-5"
                        value={formUser.rut}
                        onChange={(e) => setFormUser({ ...formUser, rut: e.target.value })}
                        required
                      />
                    </div>
                    <div className="col-md-6">
                      <label htmlFor="user-correo" className="form-label fw-semibold">Correo Institucional</label>
                      <input
                        type="email"
                        id="user-correo"
                        className="form-control"
                        value={formUser.correo}
                        onChange={(e) => setFormUser({ ...formUser, correo: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div className="row g-2 mb-3">
                    <div className="col-md-6">
                      <label htmlFor="user-nombre" className="form-label fw-semibold">Nombre</label>
                      <input
                        type="text"
                        id="user-nombre"
                        className="form-control"
                        value={formUser.nombre}
                        onChange={(e) => setFormUser({ ...formUser, nombre: e.target.value })}
                        required
                      />
                    </div>
                    <div className="col-md-6">
                      <label htmlFor="user-apellido" className="form-label fw-semibold">Apellido</label>
                      <input
                        type="text"
                        id="user-apellido"
                        className="form-control"
                        value={formUser.apellido}
                        onChange={(e) => setFormUser({ ...formUser, apellido: e.target.value })}
                        required
                      />
                    </div>
                  </div>
                  {formUser.perfil === 'ENTRENADOR' ? (
                    <div className="mb-3">
                      <label htmlFor="user-especialidad" className="form-label fw-semibold">Especialidad Deportiva</label>
                      <input
                        type="text"
                        id="user-especialidad"
                        className="form-control"
                        placeholder="Ej. Atletismo y Fisiología"
                        value={formUser.especialidad}
                        onChange={(e) => setFormUser({ ...formUser, especialidad: e.target.value })}
                        required
                      />
                    </div>
                  ) : (
                    <div className="mb-3">
                      <label htmlFor="user-matricula" className="form-label fw-semibold">Matrícula Universitaria</label>
                      <input
                        type="text"
                        id="user-matricula"
                        className="form-control"
                        placeholder="Ej. MAT-2026-099"
                        value={formUser.matricula}
                        onChange={(e) => setFormUser({ ...formUser, matricula: e.target.value })}
                        required
                      />
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowModalUsuario(false)}>Cancelar</button>
                  <button type="submit" className="btn btn-primary">Registrar Usuario</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Modal En Desarrollo Adapter */}
      <EnDesarrolloModal
        show={showAdapterModal}
        onClose={() => setShowAdapterModal(false)}
        titulo="Sincronización Intranet Académica (Patrón Adapter)"
        payloadAdapter={adapterPayload}
      />
    </main>
  );
};

export default DashboardCoordinador;
