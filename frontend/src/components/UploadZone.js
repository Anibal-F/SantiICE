import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

const UploadZone = ({ onFilesSelected }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFilesSelected(acceptedFiles);
    }
  }, [onFilesSelected]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png']
    },
    multiple: true
  });

  return (
    <div className="card p-8">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
          isDragActive 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-primary-400'
        }`}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {isDragActive ? 'Suelta los archivos aquí' : 'Sube tus tickets'}
            </h3>
            <p className="text-gray-600">
              Arrastra y suelta las imágenes de los tickets o{' '}
              <span className="text-primary-500 font-medium">haz clic para seleccionar</span>
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Formatos soportados: JPG, PNG • Múltiples archivos permitidos
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UploadZone;