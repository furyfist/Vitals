import React, { useEffect, useState } from "react";
import { useVisibility } from "@/hooks/useVisibility";
import { formatRelativeTime } from "@/lib/format/relativeTime";

export interface RelativeTimeProps {
  timestamp: number; // sec or ms
  className?: string;
}

export const RelativeTime: React.FC<RelativeTimeProps> = ({
  timestamp,
  className = "",
}) => {
  const isVisible = useVisibility();

  const ms = timestamp < 10000000000 ? timestamp * 1000 : timestamp;
  const isoString = new Date(ms).toISOString();

  const [formatted, setFormatted] = useState(() => formatRelativeTime(timestamp));

  useEffect(() => {
    if (!isVisible) return;

    setFormatted(formatRelativeTime(timestamp));

    const now = Date.now();
    const diffSec = Math.floor((now - ms) / 1000);
    const intervalMs = diffSec < 60 ? 1000 : 60000;

    const timer = setInterval(() => {
      setFormatted(formatRelativeTime(timestamp));
    }, intervalMs);

    return () => clearInterval(timer);
  }, [timestamp, ms, isVisible]);

  return (
    <time dateTime={isoString} title={isoString} className={className}>
      {formatted}
    </time>
  );
};

export default RelativeTime;
