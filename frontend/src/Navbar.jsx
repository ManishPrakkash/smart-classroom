import './Navbar.css'

const coreTabs = [
  {
    id: 'home',
    label: 'Home',
    icon: (active) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
        <path
          d="M3 12L12 4L21 12V21H15V15H9V21H3V12Z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
          fill={active ? 'currentColor' : 'none'}
          fillOpacity={active ? 0.15 : 0}
        />
      </svg>
    ),
  },
  {
    id: 'schedule',
    label: 'Schedule',
    icon: (active) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
        <rect x="3" y="4" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="1.8" fill={active ? 'currentColor' : 'none'} fillOpacity={active ? 0.12 : 0} />
        <line x1="3" y1="9" x2="21" y2="9" stroke="currentColor" strokeWidth="1.8" />
        <line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="8" cy="14" r="1.2" fill="currentColor" />
        <circle cx="12" cy="14" r="1.2" fill="currentColor" />
        <circle cx="16" cy="14" r="1.2" fill="currentColor" />
        <circle cx="8" cy="18" r="1.2" fill="currentColor" />
        <circle cx="12" cy="18" r="1.2" fill="currentColor" />
      </svg>
    ),
  },
]

const attendanceTab = {
  id: 'attendance',
  label: 'Attendance',
  icon: (active) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <rect x="4" y="2" width="16" height="20" rx="2" stroke="currentColor" strokeWidth="1.8"
        fill={active ? 'currentColor' : 'none'} fillOpacity={active ? 0.1 : 0} />
      <line x1="8" y1="7" x2="16" y2="7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <line x1="8" y1="11" x2="16" y2="11" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <polyline points="8 15 10.5 17.5 15 13" stroke="currentColor" strokeWidth="1.8"
        strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
}

const adminTab = {
  id: 'admin',
  label: 'Admin',
  icon: (active) => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.8"
        fill={active ? 'currentColor' : 'none'} fillOpacity={active ? 0.15 : 0} />
      <path d="M4 20c0-4 3.6-7 8-7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
      <path d="M17 15l1.5 1.5L21 13" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
}

export default function Navbar({ page, setPage, isAdmin }) {
  const tabs = isAdmin
    ? [...coreTabs, attendanceTab, adminTab]
    : [...coreTabs, attendanceTab]
  return (
    <nav className="navbar">
      {tabs.map(tab => {
        const active = page === tab.id
        return (
          <button
            key={tab.id}
            className={`navbar__tab ${active ? 'navbar__tab--active' : ''}`}
            onClick={() => setPage(tab.id)}
          >
            <span className="navbar__icon">{tab.icon(active)}</span>
            <span className="navbar__label">{tab.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
