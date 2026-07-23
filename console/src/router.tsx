import React from "react";
import { createBrowserRouter, Outlet } from "react-router-dom";
import AppHeader from "./components/AppHeader";
import AboutScreen from "./screens/AboutScreen";
import ConsoleScreen from "./screens/ConsoleScreen";
import NotFoundScreen from "./screens/NotFoundScreen";
import ScopesScreen from "./screens/ScopesScreen";

const AppLayout: React.FC = () => {
  return (
    <>
      <a href="#main-content" className="visually-hidden focus-visible">
        Skip to content
      </a>
      <AppHeader />
      <main id="main-content" style={{ flex: 1 }}>
        <Outlet />
      </main>
    </>
  );
};

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <ConsoleScreen /> },
      { path: "v/:verdictId", element: <ConsoleScreen /> },
      { path: "scopes", element: <ScopesScreen /> },
      { path: "about", element: <AboutScreen /> },
      { path: "*", element: <NotFoundScreen /> },
    ],
  },
]);
