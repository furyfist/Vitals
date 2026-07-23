import { TriangleAlert } from "lucide-react";
import React, { Component, type ErrorInfo, type ReactNode } from "react";
import Button from "../Button";
import CodeBlock from "../CodeBlock";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught Error Boundary caught:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: "80px var(--layout-gutter)",
            maxWidth: "600px",
            margin: "0 auto",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <TriangleAlert size={48} color="var(--color-error-dot)" />
          <h2 className="text-h2">Something broke in the console</h2>
          <p style={{ color: "var(--color-text-secondary)", fontSize: "14px" }}>
            An unexpected error occurred. You can reload the page to restore state.
          </p>

          {this.state.error && (
            <div style={{ width: "100%", textAlign: "left", marginTop: "16px" }}>
              <CodeBlock code={this.state.error.stack || this.state.error.message} />
            </div>
          )}

          <div style={{ marginTop: "16px" }}>
            <Button
              variant="primary"
              onClick={() => window.location.reload()}
            >
              Reload Page
            </Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
