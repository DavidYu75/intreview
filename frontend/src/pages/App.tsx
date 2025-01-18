import { useNavigate } from 'react-router-dom';
import './App.css';

function App() {
  const navigate = useNavigate();

  return (
    <>
       <div className="logo-main">
         <img 
           src="../public/images/Vector.svg" 
           alt="Intreview" 
           className="h-10 w-auto"
        />
      </div>
      <button onClick={() => navigate('/camera')} className="new-interview-button">
        New Intreview
      </button>
    </>
  );
}

export default App;
