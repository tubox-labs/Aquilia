import { Component, type ErrorInfo, type ReactNode } from 'react'
import { ServerErrorPage } from '../pages/ServerError'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  }

  public static getDerivedStateFromError(_: Error): State {
    return { hasError: true }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an exception:", error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return <ServerErrorPage />
    }

    return this.props.children
  }
}
