import api from './api';

export const deportesService = {
  // --- Disciplinas ---
  async getDisciplinas() {
    const res = await api.get('/disciplinas/');
    return res.data.results || res.data;
  },

  async createDisciplina(data) {
    const res = await api.post('/disciplinas/', data);
    return res.data;
  },

  async deleteDisciplina(id) {
    await api.delete(`/disciplinas/${id}/`);
  },

  // --- Usuarios (Perfiles de Entrenadores y Estudiantes) ---
  async getUsuarios(params = {}) {
    const res = await api.get('/usuarios/', { params });
    return res.data.results || res.data;
  },

  async createUsuario(data) {
    const res = await api.post('/usuarios/', data);
    return res.data;
  },

  // --- Inscripciones ---
  async getInscripciones(params = {}) {
    const res = await api.get('/inscripciones/', { params });
    return res.data.results || res.data;
  },

  async createInscripcion(data) {
    const res = await api.post('/inscripciones/', data);
    return res.data;
  },

  async deleteInscripcion(id) {
    await api.delete(`/inscripciones/${id}/`);
  },

  // --- Sesiones ---
  async getSesiones() {
    const res = await api.get('/sesiones/');
    return res.data.results || res.data;
  },

  async createSesion(data) {
    const res = await api.post('/sesiones/', data);
    return res.data;
  },

  async getNominaSesion(idSesion) {
    const res = await api.get(`/sesiones/${idSesion}/nomina_estudiantes/`);
    return res.data;
  },

  // --- Asistencia y Rendimiento (CU03 / CU05) ---
  async bulkGuardarAsistencia(idSesion, asistencias) {
    const res = await api.post('/asistencia/bulk_guardar/', {
      id_sesion: idSesion,
      asistencias,
    });
    return res.data;
  },

  // --- Portal Estudiante (RF04 / CU06 / CU07) ---
  async getPortalEstudiante() {
    const res = await api.get('/estudiantes/mi-portal/');
    return res.data;
  },

  // --- Notificaciones (CU08) ---
  async getMisNotificaciones() {
    const res = await api.get('/notificaciones/');
    return res.data.results || res.data;
  },

  async marcarNotificacionLeida(id) {
    const res = await api.post(`/notificaciones/${id}/marcar_leida/`);
    return res.data;
  },

  async marcarTodasNotificacionesLeidas() {
    const res = await api.post('/notificaciones/marcar_todas_leidas/');
    return res.data;
  },

  // --- Reportería Avanzada (RF05) ---
  async getReportes(filtros = {}) {
    const res = await api.get('/reportes/', { params: filtros });
    return res.data;
  },

  getExportarCsvUrl(filtros = {}) {
    const params = new URLSearchParams(filtros);
    params.set('export', 'csv');
    const token = sessionStorage.getItem('token');
    return `${api.defaults.baseURL}/reportes/?${params.toString()}`;
  },

  // --- Integración Adapter Intranet ---
  async sincronizarIntranetAdapter(rutEstudiante = null) {
    const res = await api.post('/adapter/sync-intranet/', {
      rut_estudiante: rutEstudiante,
    });
    return res.data;
  },
};
