import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import styled from 'styled-components';

import Header from './components/Header';
import DocumentUpload from './components/DocumentUpload';
import ProcessingStatus from './components/ProcessingStatus';
import ResultsView from './components/ResultsView';
import Analytics from './components/Analytics';
import { AppProvider } from './context/AppContext';

const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
`;

const MainContent = styled.main`
  padding-top: 80px;
  min-height: calc(100vh - 80px);
`;

function App() {
  return (
    <AppProvider>
      <Router>
        <AppContainer>
          <Header />
          <MainContent>
            <Routes>
              <Route path="/" element={<DocumentUpload />} />
              <Route path="/processing" element={<ProcessingStatus />} />
              <Route path="/results" element={<ResultsView />} />
              <Route path="/analytics" element={<Analytics />} />
            </Routes>
          </MainContent>
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme="light"
          />
        </AppContainer>
      </Router>
    </AppProvider>
  );
}

export default App; 