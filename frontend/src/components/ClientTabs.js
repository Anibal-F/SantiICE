import React from 'react';

const ClientTabs = ({ activeTab, onTabChange, oxxoCount, kioskoCount, newOxxoCount = 0, newKioskoCount = 0 }) => {
  const tabs = [
    { id: 'OXXO', label: 'OXXO', count: oxxoCount, newCount: newOxxoCount },
    { id: 'KIOSKO', label: 'KIOSKO', count: kioskoCount, newCount: newKioskoCount }
  ];

  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
              activeTab === tab.id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {tab.label}
            {tab.count > 0 && (
              <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                activeTab === tab.id
                  ? 'bg-primary-100 text-primary-600'
                  : 'bg-gray-100 text-gray-600'
              }`}>
                {tab.count}
              </span>
            )}
            {tab.newCount > 0 && (
              <span className="ml-1 w-2 h-2 bg-success-500 rounded-full animate-pulse-green" title={`${tab.newCount} nuevos tickets`}></span>
            )}
          </button>
        ))}
      </nav>
    </div>
  );
};

export default ClientTabs;