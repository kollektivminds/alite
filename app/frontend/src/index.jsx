import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './app.jsx';
import { AuthProvider } from './contexts/useAuth.js';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);
