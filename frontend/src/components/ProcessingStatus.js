import React from 'react';

const ProcessingStatus = ({ processing, message = "Procesando tickets..." }) => {
  return (
    <div className="card p-8 text-center">
      <div className="space-y-6">
        {/* Spinner */}
        <div className="mx-auto w-16 h-16">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-gray-200 border-t-primary-500"></div>
        </div>
        
        {/* Message */}
        <div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {message}
          </h3>
          <p className="text-gray-600">
            Por favor espera mientras procesamos tus archivos
          </p>
        </div>
        
        {/* Progress Info */}
        {processing && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600">
              <div className="flex justify-between items-center mb-2">
                <span>Archivos procesados:</span>
                <span className="font-medium">
                  {processing.completed || 0} de {processing.total || 0}
                </span>
              </div>
              
              {processing.current && (
                <div className="text-primary-600 font-medium">
                  Procesando: {processing.current}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingStatus;