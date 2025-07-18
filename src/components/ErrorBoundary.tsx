import React, { Component, ErrorInfo, ReactNode } from "react"
import { Alert, AlertDescription, AlertTitle } from "./ui/alert"
import { TriangleAlert } from "lucide-react"

interface Props {
  children?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50 p-4">
          <Alert variant="destructive" className="max-w-md">
            <TriangleAlert className="h-4 w-4" />
            <AlertTitle>Something went wrong!</AlertTitle>
            <AlertDescription>
              <p>An unexpected error has occurred.</p>
              {this.state.error && (
                <pre className="mt-2 whitespace-pre-wrap text-xs">
                  <code>{this.state.error.message}</code>
                </pre>
              )}
              <p className="mt-2">Please try refreshing the page or contact support if the issue persists.</p>
            </AlertDescription>
          </Alert>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
