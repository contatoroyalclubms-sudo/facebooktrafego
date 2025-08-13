import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await axios.get('/api/v1/auth/me');
      setUser(response.data);
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      delete axios.defaults.headers.common['Authorization'];
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const response = await axios.post('/api/v1/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const { access_token } = response.data;
      
      localStorage.setItem('access_token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      const userResponse = await axios.get('/api/v1/auth/me');
      setUser(userResponse.data);
      setIsAuthenticated(true);

      toast.success('Login realizado com sucesso!');
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      const message = error.response?.data?.detail || 'Erro ao fazer login';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setIsAuthenticated(false);
    toast.success('Logout realizado com sucesso!');
  };

  const register = async (userData) => {
    try {
      const response = await axios.post('/api/v1/auth/register', userData);
      toast.success('Conta criada com sucesso! Faça login para continuar.');
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Registration failed:', error);
      const message = error.response?.data?.detail || 'Erro ao criar conta';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const updateProfile = async (userData) => {
    try {
      const response = await axios.put('/api/v1/auth/me', userData);
      setUser(response.data);
      toast.success('Perfil atualizado com sucesso!');
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Profile update failed:', error);
      const message = error.response?.data?.detail || 'Erro ao atualizar perfil';
      toast.error(message);
      return { success: false, error: message };
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    register,
    updateProfile,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;
