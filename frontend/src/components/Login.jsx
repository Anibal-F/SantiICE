import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { safeErrorMessage } from '../utils/errorUtils';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, error } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await login(username, password);
      // El AuthContext se encarga de actualizar el estado de autenticación
      // y la aplicación se actualizará automáticamente
    } catch (error) {
      // El error ya se maneja en el contexto de autenticación
      setLoading(false);
    }
  };
  
  const handleOperatorLogin = async () => {
    setLoading(true);
    try {
      await login('user', 'user123');
    } catch (error) {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <div className="text-center mb-8">
          <img 
            src="/logo-santi-ice.png" 
            alt="SantiICE Logo" 
            className="h-40 mx-auto mb-4"
            onError={(e) => {
              console.error('Error cargando logo:', e);
              e.target.style.display = 'none';
            }}
          />
          <h2 className="text-2xl font-bold text-gray-800">Iniciar Sesión</h2>
          <p className="text-gray-600">Sistema SICE</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-2">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="username">
              Usuario
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="password">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              required
            />
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {safeErrorMessage(error)}
            </div>
          )}

          <div className="space-y-3">
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
            </button>
            
            <button
              type="button"
              onClick={handleOperatorLogin}
              disabled={loading}
              className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
            >
              {loading ? 'Iniciando sesión...' : 'Iniciar como Operador'}
            </button>
          </div>
        </form>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Inicia sesión como Administrador</p>
          <p className="mt-2 text-xs text-gray-400">O inicia rápido mediante "Iniciar como Operador"</p>
        </div>
      </div>
    </div>
  );
};

export default Login;