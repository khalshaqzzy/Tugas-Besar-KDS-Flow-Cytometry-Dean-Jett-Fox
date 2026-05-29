import type { DatasetSummary, FitRequest, FitResponse, HealthResponse, InitialParameters } from './types'

const DEFAULT_API_BASE_URL = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:8000'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL

async function readApiError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown }
    if (typeof payload.detail === 'string') {
      return payload.detail
    }
  } catch {
    // Fall through to the generic status message.
  }
  return `Request failed with status ${response.status}`
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)
  if (!response.ok) {
    throw new Error(await readApiError(response))
  }
  return response.json() as Promise<T>
}

export function buildFitPayload(datasetId: string, initialParameters?: InitialParameters): FitRequest {
  const payload: FitRequest = { dataset_id: datasetId }
  if (initialParameters && (initialParameters.g1_mean != null || initialParameters.g2_mean != null)) {
    payload.initial_parameters = initialParameters
  }
  return payload
}

export function buildCsvFormData(file: File, initialParameters?: InitialParameters): FormData {
  const formData = new FormData()
  formData.append('file', file)
  if (initialParameters?.g1_mean != null) {
    formData.append('g1_mean', String(initialParameters.g1_mean))
  }
  if (initialParameters?.g2_mean != null) {
    formData.append('g2_mean', String(initialParameters.g2_mean))
  }
  return formData
}

export async function fetchHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>('/health')
}

export async function fetchDatasets(): Promise<DatasetSummary[]> {
  const payload = await requestJson<{ datasets: DatasetSummary[] }>('/datasets')
  return payload.datasets
}

export async function fitDataset(datasetId: string, initialParameters?: InitialParameters): Promise<FitResponse> {
  return requestJson<FitResponse>('/fit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildFitPayload(datasetId, initialParameters)),
  })
}

export async function fitCsv(file: File, initialParameters?: InitialParameters): Promise<FitResponse> {
  return requestJson<FitResponse>('/fit/csv', {
    method: 'POST',
    body: buildCsvFormData(file, initialParameters),
  })
}
