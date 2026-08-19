import { Link, Outlet, useLocation } from "react-router-dom";

const LEFT_LINKS = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
];

const RIGHT_LINKS = [{ to: "/prices", label: "Explore Prices" }];

export function Layout() {
  const location = useLocation();
  const isLandingPage = location.pathname === "/";

  return (
    <div className={`app${isLandingPage ? " app--landing" : ""}`}>
      {!isLandingPage && <header className="site-header">
        <nav className="header-nav header-nav--left" aria-label="Primary left">
          {LEFT_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={location.pathname === to ? "is-active" : undefined}
            >
              {label}
            </Link>
          ))}
        </nav>
        <Link to="/" className="site-logo">
          Bagzine
        </Link>
        <nav className="header-nav header-nav--right" aria-label="Primary right">
          {RIGHT_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={location.pathname === to ? "is-active" : undefined}
            >
              {label}
            </Link>
          ))}
        </nav>
      </header>}

      <main className={`main${isLandingPage ? " main--landing" : ""}`}>
        <Outlet />
      </main>

      {!isLandingPage && <footer className="site-footer">
        <div className="footer-grid">
          <span aria-hidden />
          <Link to="/" className="footer-logo">
            Bagzine
          </Link>
          <a className="footer-contact" href="mailto:contact@bagazine.com">
            Contact Us
          </a>
        </div>
      </footer>}
    </div>
  );
}
