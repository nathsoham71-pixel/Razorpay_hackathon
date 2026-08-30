import { BrowserRouter, Routes, Route } from 'react-router-dom'
import NavBar from './components/layout/NavBar'
import { MerchantProvider } from './context/MerchantContext'
import DashboardPage from './pages/DashboardPage'
import MandatePage from './pages/MandatePage'
import SimulatorPage from './pages/SimulatorPage'

export default function App() {
  return (
    <MerchantProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-100">
          <NavBar />
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/mandate" element={<MandatePage />} />
            <Route path="/simulator" element={<SimulatorPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </MerchantProvider>
  )
}
