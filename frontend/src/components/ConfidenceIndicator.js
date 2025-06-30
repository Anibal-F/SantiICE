import React from 'react';
import { useConfig } from '../contexts/ConfigContext';

const ConfidenceIndicator = ({ confidence }) => {
  const { config } = useConfig();
  const getConfidenceColor = (conf) => {
    if (conf >= 90) return 'bg-success-500';
    if (conf >= 70) return 'bg-warning-500';
    return 'bg-error-500';
  };

  const getConfidenceText = (conf) => {
    if (conf >= 90) return 'Alta';
    if (conf >= 70) return 'Media';
    return 'Baja';
  };

  const getConfidenceBg = (conf) => {
    if (config.darkMode) {
      if (conf >= 90) return 'bg-green-800 text-green-100';
      if (conf >= 70) return 'bg-yellow-800 text-yellow-100';
      return 'bg-red-800 text-red-100';
    } else {
      if (conf >= 90) return 'bg-green-50 text-green-700';
      if (conf >= 70) return 'bg-yellow-50 text-yellow-700';
      return 'bg-red-50 text-red-700';
    }
  };

  return (
    <div className="flex items-center space-x-2">
      <div className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceBg(confidence)}`}>
        {getConfidenceText(confidence)}
      </div>
      <div className="flex items-center space-x-1">
        <div className={`w-16 rounded-full h-2 ${
          config.darkMode ? 'bg-gray-600' : 'bg-gray-200'
        }`}>
          <div
            className={`h-2 rounded-full ${getConfidenceColor(confidence)}`}
            style={{ width: `${confidence}%` }}
          ></div>
        </div>
        <span className={`text-xs ${
          config.darkMode ? 'text-gray-400' : 'text-gray-500'
        }`}>{confidence.toFixed(0)}%</span>
      </div>
    </div>
  );
};

export default ConfidenceIndicator;