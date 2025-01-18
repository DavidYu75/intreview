import React from 'react';
import { Settings } from 'lucide-react';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
  showRecordingTime?: boolean;
  recordingTime?: number;
}

const Layout: React.FC<LayoutProps> = ({ children}) => {

  return (
    <div className="layout-container">
      <div className="top-bar">
        <div className="top-bar-content">
          <div className="logo-container">
            <img 
              src="../public/images/Vector.svg" 
              alt="Intreview" 
              className="h-10 w-auto"  // Changed from h-8 to h-10
            />
          </div>
          <div className="top-bar-actions">
            <button>
              <Settings className="icon" />
            </button>
          </div>
        </div>
      </div>

      <main className="layout-main">{children}</main>

      <footer className="layout-footer">
        <p>&copy; 2025 | David & Bew | All Rights Reserved | FINHACKS!!</p>
      </footer>
    </div>
  );
};

export default Layout;
