import { queryClient } from "@/lib/query/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import type React from "react";

export const QueryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};
