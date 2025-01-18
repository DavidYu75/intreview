import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './pages/App.tsx'
import Camera from './pages/Camera.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Camera />
  </StrictMode>,
)
