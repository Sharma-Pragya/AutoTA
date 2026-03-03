import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight: '100vh', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontFamily: "'IBM Plex Sans', sans-serif",
          padding: 24, textAlign: 'center',
        }}>
          <div>
            <div style={{ fontSize: 32, marginBottom: 12 }}>⚠️</div>
            <h2 style={{ color: '#c0392b', marginBottom: 8 }}>Something went wrong</h2>
            <p style={{ color: '#555', marginBottom: 16, maxWidth: 400 }}>
              {this.props.message || 'An unexpected error occurred. Please refresh the page and try again.'}
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 20px', background: '#2563EB', color: '#fff',
                border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14,
              }}
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
