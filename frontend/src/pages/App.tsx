import { useNavigate } from 'react-router-dom';
import './App.css';

function App() {
  const navigate = useNavigate();

  return (
    <>
    <h1>Intreview</h1>
      <button onClick={() => navigate('/camera')} className="new-interview-button">
        New Intreview
      </button>
    </>
  );
}

export default App;
