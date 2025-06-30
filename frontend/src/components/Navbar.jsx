import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const { currentUser, logout, hasPermission } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-indigo-600">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <img
                className="h-8 w-auto"
                src="/LOGO SANTI ICE.png"
                alt="SantiICE"
              />
            </div>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link
                  to="/"
                  className="text-white hover:bg-indigo-500 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Inicio
                </Link>

                {hasPermission('upload') && (
                  <Link
                    to="/upload"
                    className="text-white hover:bg-indigo-500 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Subir Tickets
                  </Link>
                )}

                {hasPermission('conciliator') && (
                  <Link
                    to="/conciliator"
                    className="text-white hover:bg-indigo-500 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Conciliador
                  </Link>
                )}

                {hasPermission('reports') && (
                  <Link
                    to="/reports"
                    className="text-white hover:bg-indigo-500 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Reportes
                  </Link>
                )}

                {hasPermission('users') && (
                  <Link
                    to="/users"
                    className="text-white hover:bg-indigo-500 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Usuarios
                  </Link>
                )}
              </div>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="ml-4 flex items-center md:ml-6">
              <div className="ml-3 relative">
                <div>
                  <button
                    onClick={() => setIsProfileOpen(!isProfileOpen)}
                    className="max-w-xs bg-indigo-600 rounded-full flex items-center text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-indigo-600 focus:ring-white"
                  >
                    <span className="sr-only">Abrir menú de usuario</span>
                    <span className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-indigo-500">
                      <span className="text-sm font-medium leading-none text-white">
                        {currentUser?.username?.charAt(0).toUpperCase() || 'U'}
                      </span>
                    </span>
                  </button>
                </div>
                {isProfileOpen && (
                  <div className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white ring-1 ring-black ring-opacity-5 focus:outline-none">
                    <div className="px-4 py-2 text-sm text-gray-700 border-b">
                      <p className="font-medium">{currentUser?.username}</p>
                      <p className="text-xs capitalize">{currentUser?.role}</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Cerrar sesión
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="-mr-2 flex md:hidden">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="bg-indigo-600 inline-flex items-center justify-center p-2 rounded-md text-indigo-200 hover:text-white hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-indigo-600 focus:ring-white"
            >
              <span className="sr-only">Abrir menú principal</span>
              {!isMenuOpen ? (
                <svg
                  className="block h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              ) : (
                <svg
                  className="block h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {isMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link
              to="/"
              className="text-white hover:bg-indigo-500 block px-3 py-2 rounded-md text-base font-medium"
            >
              Inicio
            </Link>

            {hasPermission('upload') && (
              <Link
                to="/upload"
                className="text-white hover:bg-indigo-500 block px-3 py-2 rounded-md text-base font-medium"
              >
                Subir Tickets
              </Link>
            )}

            {hasPermission('conciliator') && (
              <Link
                to="/conciliator"
                className="text-white hover:bg-indigo-500 block px-3 py-2 rounded-md text-base font-medium"
              >
                Conciliador
              </Link>
            )}

            {hasPermission('reports') && (
              <Link
                to="/reports"
                className="text-white hover:bg-indigo-500 block px-3 py-2 rounded-md text-base font-medium"
              >
                Reportes
              </Link>
            )}

            {hasPermission('users') && (
              <Link
                to="/users"
                className="text-white hover:bg-indigo-500 block px-3 py-2 rounded-md text-base font-medium"
              >
                Usuarios
              </Link>
            )}
          </div>
          <div className="pt-4 pb-3 border-t border-indigo-700">
            <div className="flex items-center px-5">
              <div className="flex-shrink-0">
                <span className="inline-flex items-center justify-center h-10 w-10 rounded-full bg-indigo-500">
                  <span className="text-lg font-medium leading-none text-white">
                    {currentUser?.username?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </span>
              </div>
              <div className="ml-3">
                <div className="text-base font-medium leading-none text-white">
                  {currentUser?.username}
                </div>
                <div className="text-sm font-medium leading-none text-indigo-200 mt-1 capitalize">
                  {currentUser?.role}
                </div>
              </div>
            </div>
            <div className="mt-3 px-2 space-y-1">
              <button
                onClick={handleLogout}
                className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-white hover:bg-indigo-500"
              >
                Cerrar sesión
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;