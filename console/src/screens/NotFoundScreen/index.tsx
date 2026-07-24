import type React from "react";
import { Link } from "react-router-dom";

export const NotFoundScreen: React.FC = () => {
  return (
    <div className="not-found-screen" style={{ padding: "64px 24px", textAlign: "center" }}>
      <h2>404 — Page not found</h2>
      <p style={{ marginTop: "16px" }}>
        <Link to="/" style={{ color: "var(--color-accent)" }}>Back to console</Link>
      </p>
    </div>
  );
};

export default NotFoundScreen;
