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
          <span className="title">Intreview</span>
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
