import React, { useState } from 'react';
import { useConfig } from '../contexts/ConfigContext';

const DatePicker = ({ value, onChange }) => {
  const { config } = useConfig();
  const [isEditing, setIsEditing] = useState(false);
  const [dateValue, setDateValue] = useState(() => {
    // Convertir DD/MM/YYYY a YYYY-MM-DD para el input date
    if (value && value !== 'No detectada') {
      const parts = value.split('/');
      if (parts.length === 3) {
        return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
      }
    }
    return '';
  });

  const handleSave = () => {
    if (dateValue) {
      // Convertir YYYY-MM-DD a DD/MM/YYYY
      const parts = dateValue.split('-');
      const formattedDate = `${parts[2]}/${parts[1]}/${parts[0]}`;
      onChange(formattedDate);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (isEditing) {
    return (
      <div className="flex items-center space-x-2">
        <input
          type="date"
          value={dateValue}
          onChange={(e) => setDateValue(e.target.value)}
          onKeyDown={handleKeyPress}
          onBlur={handleSave}
          autoFocus
          className={`text-sm border rounded px-2 py-1 focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            config.darkMode 
              ? 'bg-gray-700 border-gray-600 text-white' 
              : 'bg-white border-gray-300'
          }`}
        />
      </div>
    );
  }

  return (
    <div
      onClick={() => setIsEditing(true)}
      className={`text-sm cursor-pointer px-2 py-1 rounded group flex items-center ${
        config.darkMode 
          ? 'text-gray-100 hover:bg-gray-700' 
          : 'text-gray-900 hover:bg-gray-100'
      }`}
    >
      <svg className="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      <span>{value}</span>
      <svg className="w-3 h-3 text-gray-400 ml-1 opacity-0 group-hover:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    </div>
  );
};

export default DatePicker;