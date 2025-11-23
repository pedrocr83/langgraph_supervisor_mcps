import axios from 'axios';
import { useAuthStore } from './authStore';

export const setupAxiosInterceptors = () => {
  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response && error.response.status === 401) {
        const token = localStorage.getItem('access_token');
        if (token) {
          useAuthStore.getState().logout();
        }
      }
      return Promise.reject(error);
    }
  );
};

