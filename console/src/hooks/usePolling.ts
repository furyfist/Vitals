import { useOnline } from "./useOnline";
import { useVisibility } from "./useVisibility";

export interface PollingState {
  isPolling: boolean;
  isPausedManual: boolean;
  isTabHidden: boolean;
  isOffline: boolean;
}

export function usePolling(isManualPaused: boolean): PollingState {
  const isVisible = useVisibility();
  const isOnline = useOnline();

  const isTabHidden = !isVisible;
  const isOffline = !isOnline;
  const isPolling = isVisible && isOnline && !isManualPaused;

  return {
    isPolling,
    isPausedManual: isManualPaused,
    isTabHidden,
    isOffline,
  };
}
