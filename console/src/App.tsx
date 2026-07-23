import type React from "react";
import { RouterProvider } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import AnnouncerProvider from "./providers/AnnouncerProvider";
import QueryProvider from "./providers/QueryProvider";
import ToastProvider from "./providers/ToastProvider";
import { router } from "./router";

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AnnouncerProvider>
        <QueryProvider>
          <ToastProvider>
            <RouterProvider router={router} />
          </ToastProvider>
        </QueryProvider>
      </AnnouncerProvider>
    </ErrorBoundary>
  );
};

export default App;
