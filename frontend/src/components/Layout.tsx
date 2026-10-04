import { NavLink, Outlet } from 'react-router-dom';

const NAV = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/tests', label: 'Tests', end: false },
  { to: '/flaky', label: 'Flaky Tests', end: true },
  { to: '/runs', label: 'Runs', end: true },
];

export function Layout() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">Flaky Test Intelligence</div>
        <nav>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="content">
        <header className="header">
          <span>QA observability for CI test suites</span>
        </header>
        <main className="main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
