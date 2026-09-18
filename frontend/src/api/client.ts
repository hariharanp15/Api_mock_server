import axios from 'axios';
const client = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api' });
client.interceptors.request.use(c => { const token = localStorage.getItem('token'); if (token) c.headers.Authorization = `Bearer ${token}`; return c; });
export default client;
