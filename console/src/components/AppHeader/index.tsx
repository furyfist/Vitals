import { Pause, Play, Search, X } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import StatusDot from "@/components/StatusDot";
import { selectMostSevereScopeState } from "@/features/verdicts/selectors";
import { useScopes } from "@/hooks/useScopes";
import { useVerdictFilters } from "@/hooks/useVerdictFilters";
import styles from "./AppHeader.module.css";

export interface AppHeaderProps {
  resultCount?: number;
}

export const AppHeader: React.FC<AppHeaderProps> = ({ resultCount }) => {
  const location = useLocation();
  const { data: scopes = [] } = useScopes();
  const severeState = selectMostSevereScopeState(scopes);

  const { filters, setSearchQuery, isPaused, togglePaused } = useVerdictFilters();

  const [localSearch, setLocalSearch] = useState(filters.q || "");
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const isConsole = location.pathname === "/" || location.pathname.startsWith("/v/");
  const isScopes = location.pathname === "/scopes";

  // Sync search param to local state
  useEffect(() => {
    setLocalSearch(filters.q || "");
  }, [filters.q]);

  // Debounce search update
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSearch !== (filters.q || "")) {
        setSearchQuery(localSearch);
      }
    }, 150);
    return () => clearTimeout(timer);
  }, [localSearch, filters.q, setSearchQuery]);

  // ⌘K / Ctrl-K / "/" keyboard shortcuts for search (§4.5 & §7.1)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
      } else if (e.key === "/" && document.activeElement?.tagName !== "INPUT") {
        e.preventDefault();
        searchInputRef.current?.focus();
      } else if (e.key === "Escape" && document.activeElement === searchInputRef.current) {
        setLocalSearch("");
        setSearchQuery("");
        searchInputRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setSearchQuery]);

  return (
    <header className={styles.header}>
      <div className={styles.left}>
        <Link to="/" className={styles.brand}>
          <StatusDot state={severeState} size={8} pulse />
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
        {/* Inline Search (§4.5) */}
        <div className={styles.searchInput}>
          <Search size={14} style={{ color: "var(--color-text-tertiary)" }} aria-hidden="true" />
          <input
            ref={searchInputRef}
            type="text"
            value={localSearch}
            onChange={(e) => setLocalSearch(e.target.value)}
            onFocus={() => setIsSearchFocused(true)}
            onBlur={() => setIsSearchFocused(false)}
            placeholder="Search sentence, version, trace…"
            style={{
              border: "none",
              background: "transparent",
              outline: "none",
              fontFamily: "var(--font-sans)",
              fontSize: "13px",
              color: "var(--color-text)",
              width: isSearchFocused || localSearch ? "220px" : "160px",
              transition: "width var(--dur-fast) var(--ease-out)",
            }}
          />
          {localSearch ? (
            <button
              type="button"
              onClick={() => {
                setLocalSearch("");
                setSearchQuery("");
              }}
              style={{
                border: "none",
                background: "none",
                cursor: "pointer",
                padding: 0,
                color: "var(--color-text-tertiary)",
              }}
              aria-label="Clear search"
            >
              <X size={14} aria-hidden="true" />
            </button>
          ) : (
            <kbd className={styles.kbdHint}>⌘K</kbd>
          )}

          {isSearchFocused && resultCount !== undefined && (
            <span
              style={{
                fontSize: "11px",
                color: "var(--color-text-tertiary)",
                marginLeft: "4px",
              }}
            >
              {resultCount} results
            </span>
          )}
        </div>

        {/* Polling Pause Toggle */}
        <button
          type="button"
          onClick={togglePaused}
          className={styles.navLink}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            border: "1px solid var(--color-border)",
            backgroundColor: isPaused ? "var(--color-warning-bg)" : "var(--color-surface)",
            color: isPaused ? "var(--color-warning-text)" : "var(--color-text-secondary)",
          }}
          title={isPaused ? "Polling paused. Click to resume." : "Click to pause polling."}
        >
          {isPaused ? <Play size={12} aria-hidden="true" /> : <Pause size={12} aria-hidden="true" />}
          <span>{isPaused ? "Paused" : "Live"}</span>
        </button>

        <Link to="/about" className={styles.navLink}>
          About
        </Link>
      </div>
    </header>
  );
};

export default AppHeader;
