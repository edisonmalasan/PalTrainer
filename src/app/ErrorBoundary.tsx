import { Component, type ErrorInfo, type ReactNode } from "react";

interface ErrorBoundaryProps {
  readonly children: ReactNode;
}

interface ErrorBoundaryState {
  readonly error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  override state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("PalTrainer render failure", error, info);
  }

  override render(): ReactNode {
    if (this.state.error) {
      return (
        <main className="min-h-[100dvh] bg-shell-panel p-8 text-shell-ink">
          <section className="mx-auto max-w-3xl border border-red-200 bg-white p-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-red-700">
              Interface Error
            </p>
            <h1 className="mt-3 text-2xl font-semibold">
              PalTrainer could not render.
            </h1>
            <p className="mt-3 text-sm leading-6 text-shell-muted">
              Restart the app and check the developer console if this keeps happening.
            </p>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
