import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex items-center justify-center min-h-[60vh]">
            <div className="bg-card p-8 rounded-lg border border-destructive max-w-lg text-center">
              <h2 className="text-xl font-bold text-destructive mb-2">Something went wrong</h2>
              <p className="text-sm text-muted-foreground mb-4">{this.state.error?.message}</p>
              <button onClick={() => this.setState({ hasError: false, error: null })} className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm">
                Try Again
              </button>
            </div>
          </div>
        )
      );
    }
    return this.props.children;
  }
}
