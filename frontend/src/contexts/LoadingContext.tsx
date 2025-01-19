import React from 'react';
import logo from '../../public/images/logoOnly.svg';
import './LoadingContext.css';

const LoadingContext: React.FC = () => {
  return (
    <div className="fixed inset-0 bg-white bg-opacity-90 z-50 flex items-center justify-center">
      <div className="text-center">
        <img src={logo} alt="Loading" className="loading-logo animate-spin" />
        <p className="loading-text">
          <span className="int-text">Int</span>
          <span className="reviewing-text">Reviewing!</span>
        </p>
      </div>
    </div>
  );
};

export default LoadingContext;
