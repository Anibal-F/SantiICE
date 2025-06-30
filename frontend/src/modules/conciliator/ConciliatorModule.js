import React, { useState, useEffect, useRef } from 'react';
import { useConfig } from '../../contexts/ConfigContext';
import apiService from '../../shared/services/ApiService';
import { useToast } from '../../hooks/useToast';
import { getBackendConfig } from '../../core/config/backendConfig';
import SessionHistoryPanel from './SessionHistoryPanel';
import SessionService from '../../services/sessions';

const ConciliatorModule = ({ onBack }) => {
  const { config, updateConfig } = useConfig();
  const { showToast } = useToast();
  
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedClient, setSelectedClient] = useState('');
  const [clients, setClients] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [sourceFile, setSourceFile] = useState(null);
  const [lookerFile, setLookerFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState({ step: '', progress: 0, message: '' });
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({ startDate: '', endDate: '' });
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);
  
  const wsRef = useRef(null);
  const sourceFileInputRef = useRef(null);
  const lookerFileInputRef = useRef(null);
  
  const steps = [
    'Seleccionar Cliente',
    'Configurar Filtros', 
    'Cargar Archivos',
    'Procesar Conciliación',
    'Revisar Resultados'
  ];

  useEffect(() => {
    loadClients();
  }, []);

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const loadClients = async () => {
    try {
      const response = await apiService.get('conciliator', 'clients');
      setClients(response.data);
    } catch (err) {
      setError('Error cargando clientes: ' + err.message);
      setClients([
        { 
          id: 'OXXO', 
          name: 'OXXO', 
          description: 'Conciliación de tickets OXXO',
          status: '✅ Funcional',
          tolerances: { percentage: 5.0, absolute: 50.0 }
        },
        { 
          id: 'KIOSKO', 
          name: 'KIOSKO', 
          description: 'Conciliación de tickets KIOSKO',
          status: '✅ Funcional',
          tolerances: { percentage: 3.0, absolute: 25.0 }
        }
      ]);
    }
  };

  const createSession = async () => {
    try {
      const response = await apiService.post('conciliator', 'session');
      const newSessionId = response.data.session_id;
      setSessionId(newSessionId);
      setupWebSocket(newSessionId);
      return newSessionId;
    } catch (err) {
      setError('Error creando sesión: ' + err.message);
      const demoSessionId = 'demo-' + Math.random().toString(36).substr(2, 9);
      setSessionId(demoSessionId);
      return demoSessionId;
    }
  };

  const setupWebSocket = (sessionId) => {
    try {
      const ws = apiService.createWebSocket('conciliator', '', sessionId);
      
      ws.onopen = () => {
        console.log('WebSocket conectado');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'progress') {
          setProgress({
            step: data.step,
            progress: data.progress,
            message: data.message
          });
        } else if (data.type === 'completed') {
          setProcessing(false);
          setResults(data.result);
          setCurrentStep(4);
          setProgress({ step: 'completed', progress: 100, message: '¡Completado!' });
          
          console.log('Guardando sesión real con cliente:', selectedClient);
          SessionService.saveSession({
            sessionId: sessionId,
            client: selectedClient,
            status: 'completed',
            summary: data.result.summary,
            records: data.result.records || [],
            sourceFile: sourceFile,
            lookerFile: lookerFile,
            dateRange: dateRange
          });
          
          showToast('Conciliación completada exitosamente', 'success');
        } else if (data.type === 'error') {
          setProcessing(false);
          setError('Error en procesamiento: ' + data.message);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Error de conexión en tiempo real');
      };
      
      wsRef.current = ws;
    } catch (err) {
      console.log('WebSocket no disponible, modo demo');
    }
  };

  const handleClientSelection = async (clientId) => {
    try {
      setSelectedClient(clientId);
      setCurrentStep(1);
      setError(null);
      await createSession();
    } catch (err) {
      setError('Error seleccionando cliente: ' + err.message);
    }
  };

  const handleDateRangeSet = () => {
    if (dateRange.startDate && dateRange.endDate) {
      setCurrentStep(2);
    }
  };

  const handleFileUpload = async (files, fileType) => {
    if (!files || files.length === 0 || !sessionId) return;
    
    const file = files[0];
    
    const allowedExtensions = ['.xlsx', '.xls', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
      setError(`Formato no permitido. Use: ${allowedExtensions.join(', ')}`);
      return;
    }
    
    if (file.size > 50 * 1024 * 1024) {
      setError('Archivo muy grande. Máximo 50MB.');
      return;
    }
    
    try {
      await apiService.uploadFile('conciliator', 'upload', file, sessionId, fileType);
      
      if (fileType === 'source') {
        setSourceFile(file);
      } else {
        setLookerFile(file);
      }
      
      setError(null);
      showToast(`Archivo ${fileType} subido correctamente`, 'success');
    } catch (err) {
      console.log('Error subiendo archivo:', err);
      if (fileType === 'source') {
        setSourceFile(file);
      } else {
        setLookerFile(file);
      }
      console.log('Modo demo: archivo guardado localmente');
    }
  };

  const handleProcessing = async () => {
    if (!sessionId || !selectedClient || !sourceFile || !lookerFile) {
      setError('Faltan archivos o cliente por seleccionar');
      return;
    }
    
    if (!dateRange.startDate || !dateRange.endDate) {
      setError('Por favor seleccione un rango de fechas');
      return;
    }
    
    try {
      setProcessing(true);
      setCurrentStep(3);
      setError(null);
      setProgress({ step: 'init', progress: 0, message: 'Iniciando...' });
      
      const config = getBackendConfig('conciliator');
      const processUrl = `${config.baseUrl}/api/conciliator/process/${sessionId}`;
      
      const response = await fetch(processUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId,
          client_type: selectedClient,
          date_range: dateRange
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Polling para obtener resultados si no hay WebSocket
      setTimeout(() => {
        pollForResults();
      }, 2000);
      
    } catch (err) {
      console.log('Backend no disponible, usando simulación');
      simulateProcessing();
    }
  };
  
  const pollForResults = async () => {
    try {
      const config = getBackendConfig('conciliator');
      const resultsUrl = `${config.baseUrl}/api/conciliator/results/${sessionId}`;
      
      const response = await fetch(resultsUrl);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.summary) {
          setProcessing(false);
          setResults(data);
          setCurrentStep(4);
          setProgress({ step: 'completed', progress: 100, message: '¡Completado!' });
          
          SessionService.saveSession({
            sessionId: sessionId,
            client: selectedClient,
            status: 'completed',
            summary: data.summary,
            records: data.records || [],
            sourceFile: sourceFile,
            lookerFile: lookerFile,
            dateRange: dateRange
          });
          
          showToast('Conciliación completada exitosamente', 'success');
        } else if (data.status === 'processing') {
          setProgress({ step: 'processing', progress: 50, message: 'Procesando...' });
          setTimeout(pollForResults, 3000);
        }
      }
    } catch (err) {
      console.log('Error obteniendo resultados:', err);
      setTimeout(pollForResults, 3000);
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'EXACT_MATCH':
        return 'Conciliado';
      case 'MISSING_IN_LOOKER':
      case 'MISSING_IN_OXXO':
      case 'MISSING_IN_KIOSKO':
        return 'Faltante';
      case 'MINOR_DIFFERENCE':
      case 'MAJOR_DIFFERENCE':
        return 'Diferencia';
      case 'WITHIN_TOLERANCE':
        return 'Tolerancia';
      default:
        return status;
    }
  };

  const simulateProcessing = () => {
    const steps = [
      { step: 'init', progress: 10, message: `Iniciando procesamiento ${selectedClient}` },
      { step: 'processing', progress: 40, message: 'Procesando archivos...' },
      { step: 'reconciliation', progress: 70, message: 'Realizando conciliación...' },
      { step: 'completed', progress: 100, message: '¡Completado!' }
    ];
    
    let currentStepIndex = 0;
    
    const interval = setInterval(() => {
      if (currentStepIndex < steps.length) {
        setProgress(steps[currentStepIndex]);
        currentStepIndex++;
      } else {
        clearInterval(interval);
        
        const sampleResults = {
          summary: {
            total_records: 15,
            exact_matches: 12,
            within_tolerance: 2,
            major_differences: 1,
            missing_records: 0,
            reconciliation_rate: 93.3,
            total_client_amount: 24587.50,
            total_looker_amount: 24491.00,
            total_difference: 96.50
          },
          records: [
            { id: '0772', client_value: 1500.00, looker_value: 1500.00, difference: 0, status: 'EXACT_MATCH', category: 'Conciliado' },
            { id: '0830', client_value: 980.50, looker_value: 985.00, difference: -4.50, status: 'WITHIN_TOLERANCE', category: 'Tolerancia' },
            { id: '1407', client_value: 1850.75, looker_value: 1950.75, difference: -100.00, status: 'MAJOR_DIFFERENCE', category: 'Diferencia' },
            { id: '2156', client_value: 0, looker_value: 750.00, difference: -750.00, status: 'MISSING_IN_OXXO', category: 'Faltante' }
          ]
        };
        
        setResults(sampleResults);
        setProcessing(false);
        setCurrentStep(4);
        
        // Guardar sesión simulada en historial
        if (sessionId) {
          SessionService.saveSession({
            sessionId: sessionId,
            client: selectedClient,
            status: 'completed',
            summary: sampleResults.summary,
            records: sampleResults.records,
            sourceFile: sourceFile,
            lookerFile: lookerFile,
            dateRange: dateRange
          });
        }
        
        showToast('Conciliación completada (simulación)', 'success');
      }
    }, 1000);
  };

  const exportToCSV = (records) => {
    const headers = ['ID', 'Valor Cliente', 'Valor Looker', 'Diferencia', 'Estado'];
    const csvContent = [
      headers.join(','),
      ...records.map(record => [
        record.id,
        record.client_value,
        record.looker_value,
        record.difference,
        record.category
      ].join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conciliacion_${selectedClient}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };
  
  const exportToExcel = (records) => {
    const csvContent = [
      'ID,Valor Cliente,Valor Looker,Diferencia,Estado',
      ...records.map(record => 
        `${record.id},${record.client_value},${record.looker_value},${record.difference},${record.category}`
      )
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'application/vnd.ms-excel' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conciliacion_${selectedClient}_${new Date().toISOString().split('T')[0]}.xlsx`;
    a.click();
    window.URL.revokeObjectURL(url);
  };
  
  const exportToPDF = (results) => {
    const htmlContent = `
      <html>
        <head>
          <title>Reporte de Conciliación - ${selectedClient}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { text-align: center; margin-bottom: 30px; }
            .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
            .summary-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f5f5f5; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Reporte de Conciliación</h1>
            <h2>${selectedClient}</h2>
            <p>Fecha: ${new Date().toLocaleDateString()}</p>
          </div>
          
          <div class="summary">
            <div class="summary-card">
              <h3>Total Registros</h3>
              <p>${results.summary.total_records}</p>
            </div>
            <div class="summary-card">
              <h3>Conciliados</h3>
              <p>${results.summary.exact_matches}</p>
            </div>
            <div class="summary-card">
              <h3>Diferencias</h3>
              <p>${results.summary.major_differences}</p>
            </div>
            <div class="summary-card">
              <h3>Tasa Éxito</h3>
              <p>${results.summary.reconciliation_rate.toFixed(1)}%</p>
            </div>
          </div>
          
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Valor ${selectedClient}</th>
                <th>Valor Looker</th>
                <th>Diferencia</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              ${results.records.map(record => `
                <tr>
                  <td>${record.id}</td>
                  <td>$${record.client_value.toLocaleString()}</td>
                  <td>$${record.looker_value.toLocaleString()}</td>
                  <td>$${record.difference.toLocaleString()}</td>
                  <td>${record.category}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </body>
      </html>
    `;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.print();
  };
  
  const printResults = (results) => {
    exportToPDF(results);
  };

  const resetSession = () => {
    setSelectedClient('');
    setSourceFile(null);
    setLookerFile(null);
    setProcessing(false);
    setResults(null);
    setCurrentStep(0);
    setSessionId(null);
    setProgress({ step: '', progress: 0, message: '' });
    setError(null);
    setDateRange({ startDate: '', endDate: '' });
    
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    if (sourceFileInputRef.current) sourceFileInputRef.current.value = '';
    if (lookerFileInputRef.current) lookerFileInputRef.current.value = '';
  };

  const FileDropzone = ({ onDrop, file, label, inputRef }) => (
    <div
      className={`border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 hover:border-blue-400 cursor-pointer ${
        file 
          ? config.darkMode 
            ? 'border-green-400 bg-green-900/20' 
            : 'border-green-400 bg-green-50'
          : config.darkMode 
            ? 'border-gray-600 bg-gray-800' 
            : 'border-gray-300 bg-white'
      }`}
      onClick={() => inputRef?.current?.click()}
      onDragOver={(e) => { e.preventDefault(); }}
      onDrop={(e) => {
        e.preventDefault();
        const files = Array.from(e.dataTransfer.files);
        onDrop(files);
      }}
    >
      <div className="flex flex-col items-center space-y-3">
        {file ? (
          <>
            <svg className="w-10 h-10 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-green-800 dark:text-green-400">{file.name}</p>
              <p className="text-xs text-green-600 dark:text-green-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          </>
        ) : (
          <>
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Arrastra tu archivo aquí</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">o haz clic para seleccionar</p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Excel (.xlsx, .xls) o CSV</p>
            </div>
          </>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        onChange={(e) => onDrop([e.target.files[0]])}
        className="hidden"
      />
    </div>
  );

  const canProceedToFiles = selectedClient && dateRange.startDate && dateRange.endDate;
  const canProcess = canProceedToFiles && sourceFile && lookerFile && !processing;

  return (
    <div className={`min-h-screen ${
      config.darkMode ? 'bg-gray-900' : 'bg-gray-50'
    }`}>
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className={`flex items-center justify-between p-4 border-b ${
          config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <div className="flex items-center space-x-4">
            <button
              onClick={onBack}
              className={`p-2 rounded-lg transition-colors ${
                config.darkMode 
                  ? 'hover:bg-gray-700 text-gray-300 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}
              title="Volver al inicio"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            
            <div>
              <h1 className={`text-xl font-bold ${
                config.darkMode ? 'text-white' : 'text-gray-900'
              }`}>
                Conciliador de Archivos
              </h1>
            </div>
          </div>
          
          <div className={`flex items-center space-x-2 transition-transform duration-300 ${
            showHistoryPanel ? 'transform translate-x-[-100px]' : ''
          }`}>
            <button
              onClick={resetSession}
              className={`p-2 rounded-lg transition-colors ${
                config.darkMode 
                  ? 'hover:bg-gray-700 text-gray-300 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}
              title="Nueva sesión"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            
            <button
              onClick={() => updateConfig({ darkMode: !config.darkMode })}
              className={`p-2 rounded-lg transition-colors ${
                config.darkMode 
                  ? 'hover:bg-gray-700 text-gray-300 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}
              title={config.darkMode ? 'Modo claro' : 'Modo oscuro'}
            >
              {config.darkMode ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
            
            <button
              onClick={() => setShowHistoryPanel(true)}
              className={`p-2 rounded-lg transition-colors ${
                config.darkMode 
                  ? 'hover:bg-gray-700 text-gray-300 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}
              title="Historial de sesiones"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className={`p-4 rounded-lg border ${
            config.darkMode 
              ? 'bg-red-900/20 border-red-800 text-red-400' 
              : 'bg-red-50 border-red-200 text-red-700'
          }`}>
            <div className="flex">
              <svg className="w-5 h-5 text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="ml-3">
                <p className="text-sm font-medium">Error</p>
                <p className="text-sm mt-1">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="ml-auto pl-3"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Progress Steps */}
        <div className={`p-4 border-b ${
          config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <div className="flex items-center justify-between overflow-x-auto px-4">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center flex-shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  index <= currentStep 
                    ? 'bg-blue-600 text-white' 
                    : config.darkMode ? 'bg-gray-700 text-gray-400' : 'bg-gray-200 text-gray-600'
                }`}>
                  {index + 1}
                </div>
                <span className={`ml-2 text-sm font-medium whitespace-nowrap ${
                  index <= currentStep 
                    ? 'text-blue-600 dark:text-blue-400' 
                    : 'text-gray-500 dark:text-gray-400'
                }`}>
                  {step}
                </span>
                {index < steps.length - 1 && (
                  <div className={`w-16 h-1 mx-4 ${
                    index < currentStep ? 'bg-blue-600' : config.darkMode ? 'bg-gray-700' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Progress Bar during processing */}
        {processing && (
          <div className={`p-6 rounded-lg ${
            config.darkMode ? 'bg-gray-800' : 'bg-white'
          } shadow-sm`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm font-medium ${
                config.darkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>{progress.message}</span>
              <span className={`text-sm ${
                config.darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>{progress.progress}%</span>
            </div>
            <div className={`w-full rounded-full h-2 ${
              config.darkMode ? 'bg-gray-700' : 'bg-gray-200'
            }`}>
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Panel de Control */}
          <div className={`w-80 flex-shrink-0 p-6 space-y-6 overflow-y-auto ${
            config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
          } border-r`}>
            <h2 className={`text-lg font-semibold ${
              config.darkMode ? 'text-white' : 'text-gray-900'
            }`}>Panel de Control</h2>
            
            {/* Selección de Cliente */}
            <div>
              <label className={`block text-sm font-medium mb-3 ${
                config.darkMode ? 'text-gray-300' : 'text-gray-700'
              }`}>
                Seleccionar Cliente
              </label>
              <div className="space-y-3">
                {clients.map((client) => (
                  <button
                    key={client.id}
                    onClick={() => handleClientSelection(client.id)}
                    disabled={processing}
                    className={`w-full p-3 rounded-lg border transition-all duration-200 ${
                      selectedClient === client.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : config.darkMode 
                          ? 'border-gray-600 hover:bg-gray-700' 
                          : 'border-gray-200 hover:bg-gray-50'
                    } ${processing ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <div className="text-center">
                      <p className={`font-medium ${
                        config.darkMode ? 'text-white' : 'text-gray-900'
                      }`}>{client.name}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Filtros de Fecha */}
            {selectedClient && (
              <div className="space-y-4">
                <h3 className={`text-sm font-medium ${
                  config.darkMode ? 'text-gray-300' : 'text-gray-700'
                }`}>Configurar Filtros</h3>
                
                <div>
                  <label className={`block text-xs font-medium mb-2 ${
                    config.darkMode ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    Fecha inicio
                  </label>
                  <input
                    type="date"
                    value={dateRange.startDate}
                    onChange={(e) => setDateRange({...dateRange, startDate: e.target.value})}
                    className={`w-full px-3 py-2 border rounded-md ${
                      config.darkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-white border-gray-300'
                    }`}
                  />
                </div>
                
                <div>
                  <label className={`block text-xs font-medium mb-2 ${
                    config.darkMode ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    Fecha fin
                  </label>
                  <input
                    type="date"
                    value={dateRange.endDate}
                    onChange={(e) => setDateRange({...dateRange, endDate: e.target.value})}
                    className={`w-full px-3 py-2 border rounded-md ${
                      config.darkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-white border-gray-300'
                    }`}
                  />
                </div>
                
                {dateRange.startDate && dateRange.endDate && (
                  <button
                    onClick={handleDateRangeSet}
                    className={`w-full text-sm py-2 px-3 rounded border transition-colors ${
                      config.darkMode 
                        ? 'bg-green-900/30 text-green-400 border-green-800 hover:bg-green-900/50'
                        : 'bg-green-50 text-green-700 border-green-300 hover:bg-green-100'
                    }`}
                  >
                    ✓ Rango confirmado: {(new Date(dateRange.endDate) - new Date(dateRange.startDate)) / (1000 * 60 * 60 * 24) + 1} días
                  </button>
                )}
              </div>
            )}

            {/* Carga de Archivos */}
            {canProceedToFiles && (
              <div className="space-y-4">
                <h3 className={`text-sm font-medium ${
                  config.darkMode ? 'text-gray-300' : 'text-gray-700'
                }`}>Cargar Archivos</h3>
                
                <div>
                  <label className={`block text-xs font-medium mb-2 ${
                    config.darkMode ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    Archivo {selectedClient}
                  </label>
                  <FileDropzone
                    onDrop={(files) => handleFileUpload(files, 'source')}
                    file={sourceFile}
                    label="source"
                    inputRef={sourceFileInputRef}
                  />
                </div>

                <div>
                  <label className={`block text-xs font-medium mb-2 ${
                    config.darkMode ? 'text-gray-400' : 'text-gray-600'
                  }`}>
                    Archivo Looker
                  </label>
                  <FileDropzone
                    onDrop={(files) => handleFileUpload(files, 'looker')}
                    file={lookerFile}
                    label="looker"
                    inputRef={lookerFileInputRef}
                  />
                </div>
              </div>
            )}

            {/* Botón de Procesamiento */}
            <button
              onClick={handleProcessing}
              disabled={!canProcess}
              className={`w-full py-3 rounded-md font-medium transition-all duration-200 ${
                canProcess
                  ? "bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg hover:shadow-xl"
                  : config.darkMode 
                    ? "bg-gray-600 text-gray-400 cursor-not-allowed"
                    : "bg-gray-300 text-gray-500 cursor-not-allowed"
              }`}
            >
              {processing ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  <span>Procesando...</span>
                </div>
              ) : (
                'Iniciar Conciliación'
              )}
            </button>

            {/* Información de sesión */}
            {sessionId && (
              <div className={`text-xs p-3 rounded space-y-1 ${
                config.darkMode 
                  ? 'text-gray-400 bg-gray-700' 
                  : 'text-gray-500 bg-gray-50'
              }`}>
                <p><strong>Sesión:</strong> {sessionId.slice(0, 8)}...</p>
                {progress.step && <p><strong>Estado:</strong> {progress.step}</p>}
                {selectedClient && <p><strong>Cliente:</strong> {selectedClient}</p>}
                {dateRange.startDate && dateRange.endDate && (
                  <p><strong>Rango:</strong> {dateRange.startDate} - {dateRange.endDate}</p>
                )}
              </div>
            )}
          </div>

          {/* Panel de Resultados */}
          <div className={`flex-1 flex flex-col p-6 ${
            config.darkMode ? 'bg-gray-900' : 'bg-gray-50'
          }`}>
            <div className="flex items-center justify-between mb-6">
              <h2 className={`text-lg font-semibold ${
                config.darkMode ? 'text-white' : 'text-gray-900'
              }`}>Resultados de Conciliación</h2>
              
              {results && (
                <div className="flex space-x-2">
                  <button
                    onClick={() => exportToCSV(results.records)}
                    className={`px-3 py-1 text-sm transition-colors ${
                      config.darkMode 
                        ? 'text-gray-300 hover:text-white hover:bg-gray-700' 
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    } rounded`}
                  >
                    📊 CSV
                  </button>
                  <button
                    onClick={() => exportToExcel(results.records)}
                    className={`px-3 py-1 text-sm transition-colors ${
                      config.darkMode 
                        ? 'text-gray-300 hover:text-white hover:bg-gray-700' 
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    } rounded`}
                  >
                    📈 Excel
                  </button>
                  <button
                    onClick={() => exportToPDF(results)}
                    className={`px-3 py-1 text-sm transition-colors ${
                      config.darkMode 
                        ? 'text-gray-300 hover:text-white hover:bg-gray-700' 
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    } rounded`}
                  >
                    📄 PDF
                  </button>
                </div>
              )}
            </div>

            {!results ? (
              <div className="flex items-center justify-center h-64">
                {processing ? (
                  <div className="text-center space-y-4">
                    <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent mx-auto" />
                    <p className={config.darkMode ? 'text-gray-400' : 'text-gray-500'}>
                      {progress.message || 'Procesando...'}
                    </p>
                  </div>
                ) : (
                  <div className="text-center">
                    <svg className={`w-16 h-16 mx-auto mb-4 ${
                      config.darkMode ? 'text-gray-600' : 'text-gray-300'
                    }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <p className={config.darkMode ? 'text-gray-400' : 'text-gray-500'}>
                      Los resultados aparecerán aquí después del procesamiento
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-6">
                {/* Resumen - Conteos */}
                <div className="flex justify-center mx-4">
                  <div className="grid grid-cols-4 gap-2 w-full max-w-5xl">
                    <div className={`p-2 rounded border ${
                      config.darkMode 
                        ? 'bg-blue-900/30 border-blue-800' 
                        : 'bg-blue-50 border-blue-200'
                    }`}>
                      <div className="text-center">
                        <p className={`text-base font-bold ${
                          config.darkMode ? 'text-blue-200' : 'text-blue-900'
                        }`}>
                          {results.summary.total_records}
                        </p>
                        <p className={`text-xs ${
                          config.darkMode ? 'text-blue-300' : 'text-blue-800'
                        }`}>Tickets Totales</p>
                      </div>
                    </div>
                    
                    <div className={`p-2 rounded border ${
                      config.darkMode 
                        ? 'bg-green-900/30 border-green-800' 
                        : 'bg-green-50 border-green-200'
                    }`}>
                      <div className="text-center">
                        <p className={`text-base font-bold ${
                          config.darkMode ? 'text-green-200' : 'text-green-900'
                        }`}>
                          {results.summary.exact_matches}
                        </p>
                        <p className={`text-xs ${
                          config.darkMode ? 'text-green-300' : 'text-green-800'
                        }`}>Tickets Conciliados</p>
                      </div>
                    </div>
                    
                    <div className={`p-2 rounded border ${
                      config.darkMode 
                        ? 'bg-red-900/30 border-red-800' 
                        : 'bg-red-50 border-red-200'
                    }`}>
                      <div className="text-center">
                        <p className={`text-base font-bold ${
                          config.darkMode ? 'text-red-200' : 'text-red-900'
                        }`}>
                          {results.summary.major_differences}
                        </p>
                        <p className={`text-xs ${
                          config.darkMode ? 'text-red-300' : 'text-red-800'
                        }`}>Tickets con Diferencia</p>
                      </div>
                    </div>
                    
                    <div className={`p-2 rounded border ${
                      config.darkMode 
                        ? 'bg-yellow-900/30 border-yellow-800' 
                        : 'bg-yellow-50 border-yellow-200'
                    }`}>
                      <div className="text-center">
                        <p className={`text-base font-bold ${
                          config.darkMode ? 'text-yellow-200' : 'text-yellow-900'
                        }`}>
                          {results.summary.missing_records}
                        </p>
                        <p className={`text-xs ${
                          config.darkMode ? 'text-yellow-300' : 'text-yellow-800'
                        }`}>Tickets Faltantes</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Resumen - Importes */}
                <div className="flex justify-center mx-4 mt-1">
                  <div className="grid grid-cols-4 gap-2 w-full max-w-5xl">
                    <div className={`p-2 rounded border ${
                      config.darkMode 
                        ? 'bg-blue-900/30 border-blue-800' 
                        : 'bg-blue-50 border-blue-200'
                    }`}>
                      <div className="text-center">
                        <p className={`text-base font-bold ${
                          config.darkMode ? 'text-blue-200' : 'text-blue-900'
                        }`}>
                          ${results.summary.total_client_amount.toLocaleString()}
                        </p>
                        <p className={`text-xs ${
                          config.darkMode ? 'text-blue-300' : 'text-blue-800'
                        }`}>Total {selectedClient}</p>
                      </div>
                    </div>
                    
                    <div className={`p-2 rounded border ${
                      config.darkMode 
                        ? 'bg-green-900/30 border-green-800' 
                        : 'bg-green-50 border-green-200'
                    }`}>
                      <div className="text-center">
                        <p className={`text-base font-bold ${
                          config.darkMode ? 'text-green-200' : 'text-green-900'
                        }`}>
                          ${results.summary.total_looker_amount.toLocaleString()}
                        </p>
                        <p className={`text-xs ${
                          config.darkMode ? 'text-green-300' : 'text-green-800'
                        }`}>Total Looker</p>
                      </div>
                    </div>
                    
                    <div className={`p-2 rounded border ${
                      config.darkMode 
                        ? 'bg-red-900/30 border-red-800' 
                        : 'bg-red-50 border-red-200'
                    }`}>
                      <div className="text-center">
                        <p className={`text-base font-bold ${
                          config.darkMode ? 'text-red-200' : 'text-red-900'
                        }`}>
                          ${results.summary.total_difference.toLocaleString()}
                        </p>
                        <p className={`text-xs ${
                          config.darkMode ? 'text-red-300' : 'text-red-800'
                        }`}>Diferencia</p>
                      </div>
                    </div>
                    
                    <div className={`p-2 rounded border ${
                      config.darkMode 
                        ? 'bg-yellow-900/30 border-yellow-800' 
                        : 'bg-yellow-50 border-yellow-200'
                    }`}>
                      <div className="text-center">
                        <p className={`text-base font-bold ${
                          config.darkMode ? 'text-yellow-200' : 'text-yellow-900'
                        }`}>
                          $0
                        </p>
                        <p className={`text-xs ${
                          config.darkMode ? 'text-yellow-300' : 'text-yellow-800'
                        }`}>Faltante</p>
                      </div>
                    </div>
                  </div>
                </div>



                {/* Tabla de Resultados */}
                <div className="flex-1 overflow-hidden mt-4">
                  <div className={`h-96 overflow-y-auto border rounded-lg ${
                    config.darkMode ? 'border-gray-600' : 'border-gray-300'
                  }`}>
                    <table className={`w-full divide-y ${
                      config.darkMode ? 'divide-gray-600' : 'divide-gray-300'
                    }`}>
                      <thead className={`sticky top-0 z-10 ${
                        config.darkMode ? 'bg-gray-700' : 'bg-gray-50'
                      }`}>
                        <tr>
                          <th className={`w-1/5 px-4 py-3 text-xs font-medium uppercase tracking-wider text-center ${
                            config.darkMode ? 'text-gray-300' : 'text-gray-500'
                          }`}>ID</th>
                          <th className={`w-1/5 px-4 py-3 text-xs font-medium uppercase tracking-wider text-center ${
                            config.darkMode ? 'text-gray-300' : 'text-gray-500'
                          }`}>Valor {selectedClient}</th>
                          <th className={`w-1/5 px-4 py-3 text-xs font-medium uppercase tracking-wider text-center ${
                            config.darkMode ? 'text-gray-300' : 'text-gray-500'
                          }`}>Valor Looker</th>
                          <th className={`w-1/5 px-4 py-3 text-xs font-medium uppercase tracking-wider text-center ${
                            config.darkMode ? 'text-gray-300' : 'text-gray-500'
                          }`}>Diferencia</th>
                          <th className={`w-1/5 px-4 py-3 text-xs font-medium uppercase tracking-wider text-center ${
                            config.darkMode ? 'text-gray-300' : 'text-gray-500'
                          }`}>Estado</th>
                        </tr>
                      </thead>
                      <tbody className={`divide-y ${
                        config.darkMode 
                          ? 'bg-gray-800 divide-gray-700' 
                          : 'bg-white divide-gray-200'
                      }`}>
                        {results.records.map((record, index) => (
                          <tr key={record.id} className={`transition-colors ${
                            record.status !== 'EXACT_MATCH' 
                              ? config.darkMode ? 'bg-red-900/20 hover:bg-red-900/30' : 'bg-red-50 hover:bg-red-100'
                              : config.darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-50'
                          }`}>
                            <td className={`w-1/5 px-4 py-4 text-sm font-medium text-center ${
                              config.darkMode ? 'text-white' : 'text-gray-900'
                            }`}>
                              <div className="truncate" title={record.id}>
                                {record.id}
                              </div>
                            </td>
                            <td className={`w-1/5 px-4 py-4 text-sm text-center ${
                              config.darkMode ? 'text-white' : 'text-gray-900'
                            }`}>
                              ${record.client_value.toLocaleString()}
                            </td>
                            <td className={`w-1/5 px-4 py-4 text-sm text-center ${
                              config.darkMode ? 'text-white' : 'text-gray-900'
                            }`}>
                              ${record.looker_value.toLocaleString()}
                            </td>
                            <td className="w-1/5 px-4 py-4 text-sm text-center">
                              <span className={`font-medium ${
                                record.difference === 0 
                                  ? 'text-green-600 dark:text-green-400' 
                                  : record.difference > 0 
                                    ? 'text-red-600 dark:text-red-400' 
                                    : 'text-orange-600 dark:text-orange-400'
                              }`}>
                                ${record.difference.toLocaleString()}
                              </span>
                            </td>
                            <td className="w-1/5 px-4 py-4 text-center">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                record.status === 'EXACT_MATCH' 
                                  ? config.darkMode 
                                    ? 'bg-green-900/30 text-green-400 border border-green-700'
                                    : 'bg-green-100 text-green-700 border border-green-300'
                                  : record.status === 'WITHIN_TOLERANCE'
                                    ? config.darkMode 
                                      ? 'bg-yellow-900/30 text-yellow-400 border border-yellow-700'
                                      : 'bg-yellow-100 text-yellow-700 border border-yellow-300'
                                    : config.darkMode 
                                      ? 'bg-red-900/30 text-red-400 border border-red-700'
                                      : 'bg-red-100 text-red-700 border border-red-300'
                              }`}>
                                {getStatusLabel(record.status)}
                              </span>
                            </td>
                          </tr>
                        ))}
                        
                          {/* Fila de Totales */}
                        {/* Fila de Totales */}
                        <tr className={`border-t-2 font-bold ${
                          config.darkMode 
                            ? 'bg-gray-700 border-gray-500 text-gray-200' 
                            : 'bg-gray-100 border-gray-400 text-gray-800'
                        }`}>
                          <td className="w-1/5 px-4 py-3 text-sm font-bold text-center">TOTALES</td>
                          <td className="w-1/5 px-4 py-3 text-sm font-bold text-center">
                            ${results.summary.total_client_amount.toLocaleString()}
                          </td>
                          <td className="w-1/5 px-4 py-3 text-sm font-bold text-center">
                            ${results.summary.total_looker_amount.toLocaleString()}
                          </td>
                          <td className="w-1/5 px-4 py-3 text-sm font-bold text-center">
                            <span className={`${
                              results.summary.total_difference === 0 
                                ? 'text-green-600 dark:text-green-400' 
                                : results.summary.total_difference > 0 
                                  ? 'text-red-600 dark:text-red-400' 
                                  : 'text-orange-600 dark:text-orange-400'
                            }`}>
                              ${results.summary.total_difference.toLocaleString()}
                            </span>
                          </td>
                          <td className="w-1/5 px-4 py-3 text-sm font-bold text-center">
                            {results.summary.total_records} registros
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
                  
                {/* Info de registros */}
                <div className={`mt-4 text-sm ${
                  config.darkMode ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  Mostrando {results.records.length} de {results.summary.total_records} registros
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Session History Panel */}
        <SessionHistoryPanel 
          isOpen={showHistoryPanel}
          onClose={() => setShowHistoryPanel(false)}
          onSessionSelect={(session) => {
            // Cargar sesión anterior
            const sessionData = SessionService.getSession(session.id);
            if (sessionData && sessionData.summary) {
              // Limpiar estado actual primero
              setResults(null);
              
              // Usar setTimeout para asegurar que el estado se limpie antes de cargar nuevos datos
              setTimeout(() => {
                const cleanResults = {
                  summary: JSON.parse(JSON.stringify(sessionData.summary)),
                  records: JSON.parse(JSON.stringify(sessionData.records || []))
                };
                
                setResults(cleanResults);
                setSelectedClient(sessionData.client);
                setCurrentStep(4);
                showToast(`Sesión ${sessionData.client} cargada`, 'success');
              }, 50);
            }
          }}
        />
      </div>
    </div>
  );
};

export default ConciliatorModule;