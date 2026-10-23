import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Font Awesome's icons, bundled rather than loaded from a CDN. Imported as plain CSS,
// outside Tailwind's layers, so its rules still win over Tailwind classes on an icon
import '@fortawesome/fontawesome-free/css/all.min.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(

  
  <StrictMode>
    <App />
  </StrictMode>
)
