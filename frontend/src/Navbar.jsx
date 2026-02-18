import './Navbar.css'

const tabs = [
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

export default function Navbar({ page, setPage }) {
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
