import axios from "axios"

/**
 * The one axios instance the app talks to the backend through. Points at
 * the FastAPI app once it exists (VITE_API_BASE_URL); until then
 * `lib/api.ts` short-circuits to mock data and this client goes unused.
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  timeout: 30_000,
})
