import React, { useState } from 'react';
import { useConfig } from '../contexts/ConfigContext';

const EditableCell = ({ value, onChange, type = 'text' }) => {
  const { config } = useConfig();
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);

  const handleSave = () => {
    onChange(editValue);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(value);
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
          type={type}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
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
      className={`text-sm cursor-pointer px-2 py-1 rounded group ${
        config.darkMode 
          ? 'text-gray-100 hover:bg-gray-700' 
          : 'text-gray-900 hover:bg-gray-100'
      }`}
    >
      <span>{value}</span>
      <svg className="w-3 h-3 text-gray-400 ml-1 opacity-0 group-hover:opacity-100 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    </div>
  );
};

export default EditableCell;