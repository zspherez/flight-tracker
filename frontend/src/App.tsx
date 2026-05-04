import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import MothersLayout from './components/MothersLayout'
import DashboardPage from './pages/DashboardPage'
import SearchPage from './pages/SearchPage'
import FlightDetailPage from './pages/FlightDetailPage'
import FourCitiesPage from './pages/FourCitiesPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/flights/:id" element={<FlightDetailPage />} />
      </Route>
      <Route element={<MothersLayout />}>
        <Route path="/mothers" element={<FourCitiesPage />} />
      </Route>
    </Routes>
  )
}
