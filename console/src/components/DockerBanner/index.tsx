import type React from "react";
import styles from "./DockerBanner.module.css";

export const DockerBanner: React.FC = () => {
  return (
    <div className={styles.banner} role="status">
      This console requires the Docker demo stack running (see{" "}
      <code>docker compose -f demo/compose.yaml up --build -d</code>) —{" "}
      <a
        className={styles.link}
        href="https://www.youtube.com/watch?v=6789BQ-O2RY"
        target="_blank"
        rel="noreferrer"
      >
        watch the demo video
      </a>
      .
    </div>
  );
};

export default DockerBanner;
