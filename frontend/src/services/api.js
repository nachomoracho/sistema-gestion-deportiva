import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Interceptor de Petición: adjuntar JWT si existe en sesión
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('token') || localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor de Respuesta: control centralizado de errores y expiración de sesión
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;

      // 401: Sesión expirada o token inválido
      if (status === 401) {
        sessionStorage.clear();
        localStorage.clear();
        if (window.location.pathname !== '/login') {
          window.location.href = '/login?expired=1';
        }
      }

      // Devolver mensaje sanitizado
      const mensaje =
        data?.mensaje ||
        (typeof data?.detalle === 'string' ? data.detalle : null) ||
        (data?.detalle ? JSON.stringify(data.detalle) : null) ||
        'Ha ocurrido un error en la comunicación con el servidor.';

      return Promise.reject(new Error(mensaje));
    }

    if (error.request) {
      return Promise.reject(new Error('No fue posible contactar al servidor. Verifique su conexión de red.'));
    }

    return Promise.reject(error);
  }
);

export default api;
