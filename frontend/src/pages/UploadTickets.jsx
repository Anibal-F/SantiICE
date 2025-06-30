import React, { useState } from 'react';
import { API_URL } from '../config';

const UploadTickets = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (files.length === 0) {
      setError('Por favor selecciona al menos un archivo');
      return;
    }

    setUploading(true);
    setError('');
    setResults(null);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await fetch(`${API_URL}/process-tickets`, {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err.message || 'Error al procesar los tickets');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <div className="px-4 py-6 sm:px-0">
        <h1 className="text-2xl font-semibold text-gray-900">Subir Tickets</h1>
        <p className="mt-1 text-sm text-gray-600">
          Sube imágenes de tickets para procesarlos con OCR
        </p>

        <div className="mt-6">
          <form onSubmit={handleSubmit}>
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Imágenes de tickets
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                      aria-hidden="true"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
                      >
                        <span>Subir archivos</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          className="sr-only"
                          multiple
                          accept="image/jpeg,image/png"
                          onChange={handleFileChange}
                        />
                      </label>
                      <p className="pl-1">o arrastra y suelta</p>
                    </div>
                    <p className="text-xs text-gray-500">
                      PNG, JPG hasta 5MB
                    </p>
                  </div>
                </div>
              </div>

              {files.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700">
                    {files.length} {files.length === 1 ? 'archivo seleccionado' : 'archivos seleccionados'}
                  </h3>
                  <ul className="mt-1 border border-gray-200 rounded-md divide-y divide-gray-200">
                    {files.map((file, index) => (
                      <li
                        key={index}
                        className="pl-3 pr-4 py-3 flex items-center justify-between text-sm"
                      >
                        <div className="w-0 flex-1 flex items-center">
                          <svg
                            className="flex-shrink-0 h-5 w-5 text-gray-400"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                            aria-hidden="true"
                          >
                            <path
                              fillRule="evenodd"
                              d="M8 4a3 3 0 00-3 3v4a5 5 0 0010 0V7a1 1 0 112 0v4a7 7 0 11-14 0V7a5 5 0 0110 0v4a3 3 0 11-6 0V7a1 1 0 012 0v4a1 1 0 102 0V7a3 3 0 00-3-3z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="ml-2 flex-1 w-0 truncate">
                            {file.name}
                          </span>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                          <span className="font-medium text-gray-500">
                            {(file.size / 1024).toFixed(0)} KB
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-red-400"
                        xmlns="http://www.w3.org/2000/svg"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">
                        Error
                      </h3>
                      <div className="mt-2 text-sm text-red-700">
                        <p>{error}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <button
                  type="submit"
                  disabled={uploading || files.length === 0}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {uploading ? 'Procesando...' : 'Procesar Tickets'}
                </button>
              </div>
            </div>
          </form>
        </div>

        {results && (
          <div className="mt-8">
            <h2 className="text-lg font-medium text-gray-900">Resultados</h2>
            <div className="mt-2 bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">
                      Total de archivos
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {results.total_files}
                    </dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">
                      Procesados correctamente
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {results.processed}
                    </dd>
                  </div>
                  <div className="sm:col-span-1">
                    <dt className="text-sm font-medium text-gray-500">
                      Con errores
                    </dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {results.errors}
                    </dd>
                  </div>
                </dl>
              </div>
              <div className="border-t border-gray-200">
                <div className="px-4 py-5 sm:px-6">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Detalle de tickets
                  </h3>
                </div>
                <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
                  <dl className="sm:divide-y sm:divide-gray-200">
                    {results.results.map((result, index) => (
                      <div key={index} className="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt className="text-sm font-medium text-gray-500">
                          {result.filename}
                        </dt>
                        <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                          <div className="flex items-center">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              result.status === 'processed' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {result.status === 'processed' ? 'Procesado' : 'Error'}
                            </span>
                            {result.status === 'error' && (
                              <span className="ml-2 text-sm text-red-600">
                                {result.error}
                              </span>
                            )}
                            {result.status === 'processed' && (
                              <span className="ml-2 text-sm text-gray-600">
                                {result.sucursal_type} - {result.productos?.length || 0} productos
                              </span>
                            )}
                          </div>
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadTickets;