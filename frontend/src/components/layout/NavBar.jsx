import { NavLink } from 'react-router-dom'
import { MerchantSelector } from '../../context/MerchantContext'

const linkClass = ({ isActive }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium transition ${
    isActive
      ? 'bg-indigo-600 text-white shadow-sm'
      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
  }`

export default function NavBar() {
  return (
    <header className="border-b border-slate-200 bg-white shadow-sm">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-slate-400">
            Merchant Agent Platform
          </p>
          <h1 className="text-lg font-semibold text-slate-900">Demo Console</h1>
        </div>
        <nav className="flex flex-wrap gap-1">
          <NavLink to="/" end className={linkClass}>
            Dashboard
          </NavLink>
          <NavLink to="/mandate" className={linkClass}>
            Mandate
          </NavLink>
          <NavLink to="/simulator" className={linkClass}>
            Buyer Simulator
          </NavLink>
        </nav>
        <MerchantSelector />
      </div>
    </header>
  )
}
