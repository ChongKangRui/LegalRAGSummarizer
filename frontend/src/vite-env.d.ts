/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the FastAPI backend, e.g. http://localhost:8000. */
  readonly VITE_API_BASE_URL?: string
  /**
   * "false" to call the real backend instead of the built-in mock data.
   * Defaults to mocks (true) so the UI works with no backend running.
   */
  readonly VITE_USE_MOCKS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
