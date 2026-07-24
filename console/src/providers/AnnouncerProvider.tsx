import React, { createContext, useContext, useRef, useState } from "react";

interface AnnouncerContextValue {
  announcePolite: (message: string) => void;
  announceAssertive: (message: string) => void;
}

const AnnouncerContext = createContext<AnnouncerContextValue>({
  announcePolite: () => {},
  announceAssertive: () => {},
});

export const useAnnouncer = () => useContext(AnnouncerContext);

export const AnnouncerProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [politeMessage, setPoliteMessage] = useState("");
  const [assertiveMessage, setAssertiveMessage] = useState("");

  const lastPoliteTime = useRef(0);

  const announcePolite = (message: string) => {
    const now = Date.now();
    if (now - lastPoliteTime.current >= 3000) {
      lastPoliteTime.current = now;
      setPoliteMessage(message);
    }
  };

  const announceAssertive = (message: string) => {
    setAssertiveMessage(message);
  };

  return (
    <AnnouncerContext.Provider value={{ announcePolite, announceAssertive }}>
      {children}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="visually-hidden"
      >
        {politeMessage}
      </div>
      <div
        aria-live="assertive"
        aria-atomic="true"
        className="visually-hidden"
      >
        {assertiveMessage}
      </div>
    </AnnouncerContext.Provider>
  );
};
