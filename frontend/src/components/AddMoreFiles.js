import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

const AddMoreFiles = ({ onFilesAdded, isProcessing }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0 && !isProcessing) {
      onFilesAdded(acceptedFiles);
    }
  }, [onFilesAdded, isProcessing]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png']
    },
    multiple: true,
    disabled: isProcessing
  });

  return (
    <div className="card p-4 border-2 border-dashed border-gray-300 hover:border-primary-400 transition-colors">
      <div
        {...getRootProps()}
        className={`text-center cursor-pointer ${
          isProcessing ? 'opacity-50 cursor-not-allowed' : ''
        } ${isDragActive ? 'bg-primary-50' : ''}`}
      >
        <input {...getInputProps()} />
        
        <div className="flex items-center justify-center space-x-3">
          {isProcessing ? (
            <div className="animate-spin rounded-full h-6 w-6 border-2 border-gray-300 border-t-primary-500"></div>
          ) : (
            <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
          )}
          <div>
            <span className="text-sm font-medium text-gray-700">
              {isProcessing ? 'Procesando nuevos tickets...' : 'Agregar más tickets'}
            </span>
            <p className="text-xs text-gray-500 mt-1">
              {isProcessing ? 'Por favor espera' : isDragActive ? 'Suelta aquí' : 'Arrastra archivos o haz clic'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddMoreFiles;