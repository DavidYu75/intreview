import { useNavigate } from 'react-router-dom';
import './App.css';

function App() {
  const navigate = useNavigate();

  return (
    <>
      <div className="logo-main">
        <img 
          src="../public/images/logov2.svg" 
          alt="Intreview" 
          className="h-10 w-auto"
        />
      </div>
      <h1 className="welcome-text">Welcome Back! David</h1>
      <div className="button-container">
        <button onClick={() => navigate('/camera')} className="new-intreview-button">
          New Intreview
        </button>
      </div>
    </>
  );
}

export default App;
