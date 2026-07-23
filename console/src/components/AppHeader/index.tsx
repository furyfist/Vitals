import type React from "react";
import { Link, useLocation } from "react-router-dom";
import styles from "./AppHeader.module.css";

export const AppHeader: React.FC = () => {
  const location = useLocation();

  const isConsole = location.pathname === "/" || location.pathname.startsWith("/v/");
  const isScopes = location.pathname === "/scopes";

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <Link to="/" className={styles.brand}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              backgroundColor: "var(--color-steady-dot)",
              display: "inline-block",
            }}
            aria-label="Scope state STEADY"
          />
          vitals
        </Link>
      </div>

      <nav className={styles.nav} aria-label="Main Navigation">
        <Link
          to="/"
          className={`${styles.navLink} ${isConsole ? styles.activeNavLink : ""}`}
        >
          Console
        </Link>
        <Link
          to="/scopes"
          className={`${styles.navLink} ${isScopes ? styles.activeNavLink : ""}`}
        >
          Scopes
        </Link>
      </nav>

      <div className={styles.right}>
        <div className={styles.searchInput}>
          <span>Search...</span>
          <kbd className={styles.kbdHint}>⌘K</kbd>
        </div>
        <Link to="/about" className={styles.navLink}>
          About
        </Link>
      </div>
    </header>
  );
};

export default AppHeader;
