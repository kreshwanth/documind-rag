import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('documind_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Response interceptor: handle 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('documind_token');
      localStorage.removeItem('documind_user');
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  register: (data) => apiClient.post('/auth/register', data),
  login: (data) => apiClient.post('/auth/login', data),
  getMe: () => apiClient.get('/auth/me'),
};

export const documentApi = {
  list: () => apiClient.get('/documents'),
  get: (id) => apiClient.get(`/documents/${id}`),
  delete: (id) => apiClient.delete(`/documents/${id}`),
  process: (id) => apiClient.post(`/documents/${id}/process`),
  getStatus: (id) => apiClient.get(`/documents/${id}/status`),
  upload: (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    });
  },
};

export const chatApi = {
  chat: (data) => apiClient.post('/chat', data),
};

export const ragApi = {
  query: (data) => apiClient.post('/chat', data),
  chat: (data) => apiClient.post('/chat', data),
  searchChunks: (data) => apiClient.post('/search', data),
};

export const searchApi = {
  search: (data) => apiClient.post('/search', data),
};

export const conversationApi = {
  list: () => apiClient.get('/conversations'),
  create: (data) => apiClient.post('/conversations', data),
  get: (id) => apiClient.get(`/conversations/${id}`),
  delete: (id) => apiClient.delete(`/conversations/${id}`),
};

export const dashboardApi = {
  getStats: () => apiClient.get('/dashboard/stats'),
};

export const healthApi = {
  check: () => apiClient.get('/health'),
};

export default apiClient;
