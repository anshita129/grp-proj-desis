import axios from 'axios';

// Read Django's csrftoken cookie
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

const api = axios.create({
  baseURL: '/api/learning',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

// Attach CSRF token to every mutating request
api.interceptors.request.use(config => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    config.headers['X-CSRFToken'] = getCookie('csrftoken');
  }
  return config;
});

// ── Modules ──
export const getModules       = ()     => api.get('/modules/');
export const getModule        = (slug) => api.get(`/modules/${slug}/`);
export const getModuleProgress= (slug) => api.get(`/modules/${slug}/progress/`);

// ── Lessons ──
export const getLesson        = (id)   => api.get(`/lessons/${id}/`);
export const completeLesson   = (id)   => api.post(`/lessons/${id}/complete/`);

// ── Quizzes ──
export const getQuiz          = (slug) => api.get(`/modules/${slug}/quiz/`);
export const submitAttempt    = (qid, data) => api.post(`/quizzes/${qid}/attempt/`, data);
export const getAttempt       = (id)   => api.get(`/attempts/${id}/`);
export const getMyAttempts    = (qid)  => api.get(`/quizzes/${qid}/my-attempts/`);

// ── Badges ──
export const getBadges        = ()     => api.get('/badges/');
export const getMyBadges      = ()     => api.get('/badges/mine/');

export default api;
