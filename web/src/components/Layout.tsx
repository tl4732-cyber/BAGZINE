import { Link, Outlet, useLocation } from "react-router-dom";

const LEFT_LINKS = [
  { to: "/prices", label: "explore" },
  { to: "/the-brand", label: "the brand" },
  { to: "/tech-specs", label: "tech specs" },
];

const RIGHT_LINKS = [
  { to: "/the-creator", label: "the creator" },
  { to: "/contact", label: "contact" },
];

function navClass(pathname: string, to: string) {
  return pathname === to || (to !== "/" && pathname.startsWith(`${to}/`))
    ? "is-active"
    : undefined;
}

export function Layout() {
  const location = useLocation();
  const isLandingPage = location.pathname === "/";
  const isStoryPage = location.pathname === "/the-brand" || location.pathname === "/the-creator";

  return (
    <div
      className={`app${isLandingPage ? " app--landing" : ""}${isStoryPage ? " app--brand" : ""}`}
    >
      <header className="site-header">
        <nav className="header-nav header-nav--left" aria-label="Primary left">
          {LEFT_LINKS.map(({ to, label }) => (
            <Link key={to} to={to} className={navClass(location.pathname, to)}>
              {label}
            </Link>
          ))}
        </nav>
        <Link to="/" className="site-logo">
          Bagzine
        </Link>
        <nav className="header-nav header-nav--right" aria-label="Primary right">
          {RIGHT_LINKS.map(({ to, label }) => (
            <Link key={to} to={to} className={navClass(location.pathname, to)}>
              {label}
            </Link>
          ))}
        </nav>
      </header>

      <main className={`main${isLandingPage ? " main--landing" : ""}`}>
        <Outlet />
      </main>
    </div>
  );
}
