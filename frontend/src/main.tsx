import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import App from './pages/App';
import Camera from './pages/Camera';
import ResultsPage from './pages/Results';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/camera" element={<Camera />} />
          <Route path="/results" element={<ResultsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  </React.StrictMode>
);
