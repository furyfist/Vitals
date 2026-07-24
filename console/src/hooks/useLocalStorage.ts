import { useCallback, useState } from "react";

export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T | ((val: T) => T)) => void] {
  const fullKey = key.startsWith("vitals.console.") ? key : `vitals.console.${key}`;

  const readValue = useCallback((): T => {
    if (typeof window === "undefined") return initialValue;
    try {
      const item = window.localStorage.getItem(fullKey);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${fullKey}":`, error);
      return initialValue;
    }
  }, [fullKey, initialValue]);

  const [storedValue, setStoredValue] = useState<T>(readValue);

  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      if (typeof window === "undefined") return;
      try {
        const newValue = value instanceof Function ? value(storedValue) : value;
        window.localStorage.setItem(fullKey, JSON.stringify(newValue));
        setStoredValue(newValue);
      } catch (error) {
        console.warn(`Error setting localStorage key "${fullKey}":`, error);
      }
    },
    [fullKey, storedValue]
  );

  return [storedValue, setValue];
}
