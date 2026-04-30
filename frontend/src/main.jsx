import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import Home from './Home.jsx'
import AnalyzePage from './App.jsx'
import RelationPage from './Relation.jsx'
import PaymentResult from './PaymentResult.jsx'
import Terms from './Terms.jsx'
import Privacy from './Privacy.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analyze" element={<AnalyzePage />} />
        <Route path="/relation" element={<RelationPage />} />
        <Route path="/payment/result" element={<PaymentResult />} />
        <Route path="/terms" element={<Terms />} />
        <Route path="/privacy" element={<Privacy />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
