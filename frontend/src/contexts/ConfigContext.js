import React, { createContext, useContext, useState, useEffect } from 'react';

const ConfigContext = createContext();

export const useConfig = () => {
  const context = useContext(ConfigContext);
  if (!context) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
};

export const ConfigProvider = ({ children }) => {
  const [config, setConfig] = useState({
    // Configuraciones de confianza
    allowHighConfidenceEdit: true,
    minConfidenceThreshold: 70,
    
    // Tema
    darkMode: false,
    
    // Catálogos
    sucursales: {
      OXXO: [
        'Acapulco', 'Atlantico', 'Bonfil', 'Calandrias', 'Cerro Colorado', 'Coto 12', 'Del Sol', 'Ejercito', 'Ejercito Mexicano', 'El Conchi', 'El Tiburon', 'El Toreo', 'Escoboza', 'Garcia', 'Gaviotas', 'Girasoles', 'Hospital Militar', 'Infante', 'Jardines Riviera', 'Las Garzas', 'Los Portales', 'Los Sauces', 'Macias', 'Maxipista', 'Miramar', 'Najera', 'Nus Wyndham', 'Perez Arce', 'Poniente 14', 'Portomolino', 'Potrerillo Norte', 'Presidencia', 'Real del Valle', 'Rio Elota', 'Satelite', 'Sur 16', 'Sábalo', 'Talleres', 'Telegrafos', 'Telleria', 'Urias', 'Valle del Sol', 'Venneto', 'Villareal', 'Villas del Rey', 'Zaragoza', 'Zaragoza II'
      ],
      KIOSKO: [
        '20 De Noviembre', 'Acaponeta', 'Alameda', 'Alarcon', 'Alfredo Bonfil', 'Azalea', 'Bicentenario', 'Camaron Sabalo', 'Central Mazatlan', 'Cerritos', 'Cerritos Playa', 'Circunvalacion', 'City Express', 'Del Delfin', 'El Cid', 'El Marino', 'El Walamo', 'Emilio Barragan', 'Estadio', 'Flores Magon', 'Francisco Perez', 'Gabriel Leyva', 'Gas Cardones', 'Gas Cerritos', 'Gas Concordia', 'Gas Habal', 'Gas La Marina', 'Gasmaz', 'Gasmaz Colosio', 'Independencia', 'Insurgentes', 'Insurgentes Mazatlan', 'Jabalies', 'Jaripillo', 'Juarez', 'Juarez Internacional', 'La Marina', 'Laguna el Rosario', 'Las Americas', 'Laureles', 'Libertad Expresion', 'Lomas de Mazatlan', 'Lopez Portillo', 'Madero Villa Union', 'Magnolia', 'Malecon Escuinapa', 'Malecon Mazatlan', 'Miguel Aleman', 'Miguel Hidalgo', 'Munich', 'Mutualismo', 'Occidental', 'Olimpica', 'Paseo Claussen', 'Paseo Olas Altas', 'Paseo del Centenario', 'Paseo del Pacifico', 'Perez Arce', 'Pino Suarez', 'Prados del Sol', 'Presidentes', 'Querétaro', 'Rafael Buelna', 'Real Pacifico', 'Rio Chachalacas', 'Sabalo Country', 'Salvador Allende', 'Santa Rosa', 'Santa Teresa', 'Solidaridad', 'Tecuala', 'Universo', 'Urbivillas', 'Valle de Urias', 'Villa Galaxia', 'Villas del Rey', 'Villas del Sol', 'Zaragoza', 'Zona Dorada'
      ]
    },
    
    // Precios por sucursal y cliente
    precios: {
      default: {
        OXXO: {
          '5kg': 17.5,
          '15kg': 37.5
        },
        KIOSKO: {
          '5kg': 16.0,
          '15kg': 45.0
        }
      },
      OXXO: {
        'Girasoles': { '5kg': 17.5, '15kg': 37.5 },
        'Zaragoza': { '5kg': 17.5, '15kg': 37.5 },
        // Precios preferenciales para algunas sucursales
        'Atlantico': { '5kg': 17.0, '15kg': 37.0 }
      },
      KIOSKO: {
        '20 De Noviembre': { '5kg': 15.0, '15kg': 45.0 },
        'Gas Cardones': { '5kg': 15.0, '15kg': 45.0 }
      }
    }
  });

  // Cargar configuración del localStorage
  useEffect(() => {
    const savedConfig = localStorage.getItem('santiice-config');
    if (savedConfig) {
      try {
        const parsedConfig = JSON.parse(savedConfig);
        setConfig(prev => ({ ...prev, ...parsedConfig }));
      } catch (error) {
        console.error('Error loading config:', error);
      }
    } else {
      // Si no hay configuración guardada, usar la configuración completa por defecto
      console.log('Usando configuración completa por defecto');
    }
  }, []);

  // Guardar configuración en localStorage
  const updateConfig = (newConfig) => {
    const updatedConfig = { ...config, ...newConfig };
    setConfig(updatedConfig);
    localStorage.setItem('santiice-config', JSON.stringify(updatedConfig));
  };

  const addSucursal = (tipo, nombre) => {
    const newSucursales = {
      ...config.sucursales,
      [tipo]: [...config.sucursales[tipo], nombre]
    };
    updateConfig({ sucursales: newSucursales });
  };

  const updatePrecio = (cliente, sucursal, tipo, precio) => {
    const newPrecios = {
      ...config.precios,
      [cliente]: {
        ...config.precios[cliente],
        [sucursal]: {
          ...config.precios[cliente]?.[sucursal],
          [tipo]: precio
        }
      }
    };
    updateConfig({ precios: newPrecios });
  };

  const getPrecio = (cliente, sucursal, tipo) => {
    return config.precios[cliente]?.[sucursal]?.[tipo] || 
           config.precios.default[cliente]?.[tipo] || 
           config.precios.default.OXXO[tipo] || 
           (tipo === '5kg' ? 17.5 : 37.5);
  };

  const toggleDarkMode = () => {
    updateConfig({ darkMode: !config.darkMode });
  };

  return (
    <ConfigContext.Provider value={{
      config: { ...config, toggleDarkMode },
      updateConfig,
      addSucursal,
      updatePrecio,
      getPrecio
    }}>
      {children}
    </ConfigContext.Provider>
  );
};