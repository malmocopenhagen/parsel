import React, { createContext, useContext, useReducer } from 'react';

const AppContext = createContext();

const initialState = {
  uploadedFile: null,
  processingStatus: 'idle', // idle, uploading, processing, completed, error
  extractionResults: null,
  accuracyMetrics: null,
  currentStep: 0,
  totalSteps: 4,
  error: null,
  processingProgress: {
    ocr: 0,
    tableDetection: 0,
    validation: 0,
    csvGeneration: 0
  }
};

const appReducer = (state, action) => {
  switch (action.type) {
    case 'SET_UPLOADED_FILE':
      return {
        ...state,
        uploadedFile: action.payload,
        processingStatus: 'uploading'
      };
    
    case 'SET_PROCESSING_STATUS':
      return {
        ...state,
        processingStatus: action.payload
      };
    
    case 'SET_EXTRACTION_RESULTS':
      return {
        ...state,
        extractionResults: action.payload,
        processingStatus: 'completed'
      };
    
    case 'SET_ACCURACY_METRICS':
      return {
        ...state,
        accuracyMetrics: action.payload
      };
    
    case 'SET_CURRENT_STEP':
      return {
        ...state,
        currentStep: action.payload
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        processingStatus: 'error'
      };
    
    case 'SET_PROCESSING_PROGRESS':
      return {
        ...state,
        processingProgress: {
          ...state.processingProgress,
          ...action.payload
        }
      };
    
    case 'RESET_STATE':
      return {
        ...initialState
      };
    
    default:
      return state;
  }
};

export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const value = {
    ...state,
    dispatch
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}; 