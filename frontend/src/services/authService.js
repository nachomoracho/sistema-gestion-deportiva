import api from './api';

export const authService = {
  async login(rut_o_correo, clave) {
    const response = await api.post('/auth/login/', { rut_o_correo, clave });
    const { access, refresh, usuario } = response.data;
    
    sessionStorage.setItem('token', access);
    sessionStorage.setItem('refreshToken', refresh);
    sessionStorage.setItem('usuario', JSON.stringify(usuario));

    return usuario;
  },

  async logout() {
    try {
      await api.post('/auth/logout/');
    } catch {
      // Ignorar error al cerrar sesión
    } finally {
      sessionStorage.clear();
      localStorage.clear();
    }
  },

  async changePassword(clave_actual, clave_nueva) {
    const response = await api.post('/auth/change-password/', { clave_actual, clave_nueva });
    return response.data;
  },

  async getMe() {
    const response = await api.get('/auth/me/');
    return response.data;
  },

  getCurrentUser() {
    const stored = sessionStorage.getItem('usuario');
    if (!stored) return null;
    try {
      return JSON.parse(stored);
    } catch {
      return null;
    }
  },

  isAuthenticated() {
    return Boolean(sessionStorage.getItem('token'));
  },

  getUserRole() {
    const user = this.getCurrentUser();
    return user?.perfil || null;
  },
};
