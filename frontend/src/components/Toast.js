import React, { useEffect } from 'react';
import { useConfig } from '../contexts/ConfigContext';

const Toast = ({ message, type = 'info', isVisible, onClose, duration = 4000 }) => {
  const { config } = useConfig();
  useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [isVisible, duration, onClose]);

  if (!isVisible) return null;

  const getToastStyles = () => {
    const baseStyles = config.darkMode ? 'border shadow-lg' : 'border shadow-lg';
    
    switch (type) {
      case 'success':
        return config.darkMode 
          ? `${baseStyles} bg-green-800 border-green-600 text-green-100`
          : `${baseStyles} bg-green-50 border-green-200 text-green-800`;
      case 'error':
        return config.darkMode 
          ? `${baseStyles} bg-red-800 border-red-600 text-red-100`
          : `${baseStyles} bg-red-50 border-red-200 text-red-800`;
      case 'warning':
        return config.darkMode 
          ? `${baseStyles} bg-yellow-800 border-yellow-600 text-yellow-100`
          : `${baseStyles} bg-yellow-50 border-yellow-200 text-yellow-800`;
      default:
        return config.darkMode 
          ? `${baseStyles} bg-blue-800 border-blue-600 text-blue-100`
          : `${baseStyles} bg-blue-50 border-blue-200 text-blue-800`;
    }
  };

  const getIcon = () => {
    const getIconColor = (baseColor) => {
      return config.darkMode ? `text-${baseColor}-200` : `text-${baseColor}-600`;
    };

    switch (type) {
      case 'success':
        return (
          <svg className={`w-5 h-5 ${getIconColor('green')}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'error':
        return (
          <svg className={`w-5 h-5 ${getIconColor('red')}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      case 'warning':
        return (
          <svg className={`w-5 h-5 ${getIconColor('yellow')}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        );
      default:
        return (
          <svg className={`w-5 h-5 ${getIconColor('blue')}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in">
      <div className={`flex items-center p-4 border rounded-lg shadow-lg max-w-sm ${getToastStyles()}`}>
        <div className="flex-shrink-0">
          {getIcon()}
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium">{typeof message === 'string' ? message : 'Error occurred'}</p>
        </div>
        <button
          onClick={onClose}
          className={`ml-4 flex-shrink-0 ${
            config.darkMode 
              ? 'text-gray-300 hover:text-gray-100' 
              : 'text-gray-400 hover:text-gray-600'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default Toast;