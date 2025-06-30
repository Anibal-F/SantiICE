import React from 'react';
import { safeErrorMessage } from '../utils/errorUtils';

const ResultsSummary = ({ results, onStartOver }) => {
  // Manejar caso donde results es null o undefined
  if (!results) {
    return (
      <div className="card p-8 text-center">
        <div className="text-gray-500">
          No hay resultados para mostrar
        </div>
        <button
          onClick={onStartOver}
          className="btn-primary mt-4"
        >
          Procesar tickets
        </button>
      </div>
    );
  }

  const summary = results.summary || {};
  const resultsList = results.results || [];

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-gray-900">{summary.total || 0}</div>
          <div className="text-sm text-gray-600">Total</div>
        </div>
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-success-600">{summary.success || 0}</div>
          <div className="text-sm text-success-600">Exitosos</div>
        </div>
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-error-600">{summary.errors || 0}</div>
          <div className="text-sm text-error-600">Errores</div>
        </div>
        <div className="card p-6 text-center">
          <div className="text-3xl font-bold text-warning-600">{summary.duplicated || 0}</div>
          <div className="text-sm text-warning-600">Duplicados</div>
        </div>
      </div>

      {/* Results Details */}
      <div className="card">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Detalles del procesamiento
          </h3>
        </div>
        
        <div className="divide-y divide-gray-200">
          {resultsList.map((result, index) => (
            <div key={result.id || index} className="p-6 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`w-3 h-3 rounded-full ${
                  result.status === 'success' 
                    ? 'bg-success-500' 
                    : result.duplicated 
                    ? 'bg-warning-500'
                    : 'bg-error-500'
                }`}></div>
                <div>
                  <div className="font-medium text-gray-900">{result.filename || 'Unknown file'}</div>
                  <div className="text-sm text-gray-600">
                    {safeErrorMessage(result.message || result.details || 'Processing result')}
                  </div>
                </div>
              </div>
              
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                result.status === 'success' 
                  ? 'bg-success-50 text-success-700' 
                  : result.duplicated
                  ? 'bg-warning-50 text-warning-700'
                  : 'bg-error-50 text-error-700'
              }`}>
                {result.status === 'success' 
                  ? 'Exitoso' 
                  : result.duplicated 
                  ? 'Duplicado'
                  : 'Error'
                }
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="text-center">
        <button
          onClick={onStartOver}
          className="btn-primary"
        >
          Procesar más tickets
        </button>
      </div>
    </div>
  );
};

export default ResultsSummary;