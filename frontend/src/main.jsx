import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import Home from './Home.jsx'
import AnalyzePage from './App.jsx'
import PaymentResult from './PaymentResult.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analyze" element={<AnalyzePage />} />
        <Route path="/payment/result" element={<PaymentResult />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
