import type React from "react";
import StatusDot from "@/components/StatusDot";

export interface LivePulseDotProps {
  isPolling: boolean;
  isPaused: boolean;
  isOffline: boolean;
  isReconnecting: boolean;
}

export const LivePulseDot: React.FC<LivePulseDotProps> = ({
  isPolling,
  isPaused,
  isOffline,
  isReconnecting,
}) => {
  if (isOffline || isReconnecting) {
    return <StatusDot color="var(--color-text-tertiary)" size={8} label="Reconnecting" />;
  }

  if (isPaused || !isPolling) {
    return <StatusDot color="var(--color-warming-dot)" size={8} label="Paused" />;
  }

  return <StatusDot state="STEADY" size={8} pulse label="Live monitoring active" />;
};

export default LivePulseDot;
