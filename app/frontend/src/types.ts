export type HealthResponse = {
  status: string
  service: string
  model: string
}

export type DatasetSummary = {
  id: string
  name: string
  source_file: string
  condition: string
  timepoint_hours: string
  channel: string
  events_total: number
  events_used: number
  bin_count: number
  csv_path: string
}

export type InitialParameters = {
  g1_mean?: number | null
  g2_mean?: number | null
}

export type FitRequest = {
  dataset_id?: string
  histogram?: {
    bins: number[]
    counts: number[]
  }
  initial_parameters?: InitialParameters
}

export type FitMetrics = {
  sse: number
  rmse: number
  r_squared: number | null
  weighted_sse: number
  reduced_chi_square: number
}

export type FitParameters = {
  g1_mean: number
  g1_sigma: number
  g2_mean: number
  g2_sigma: number
  g1_mean_scaled: number
  g2_mean_scaled: number
  g1_sigma_scaled: number
  g2_sigma_scaled: number
  s_polynomial_coefficients: number[]
  g2_g1_ratio: number
  g1_cv: number
  debris_area: number
  debris_percent_of_total_signal: number
}

export type FitSeries = {
  bins: number[]
  observed: number[]
  fit_total: number[]
  g1: number[]
  s: number[]
  s_unbroadened: number[]
  g2_m: number[]
  residual: number[]
  weighted_residual: number[]
  debris: number[]
  background: number[]
}

export type QualityFlag = {
  key: string
  severity: 'info' | 'caution' | 'warning'
  label: string
  message: string
}

export type FitResponse = {
  fit_id: string
  model_info: {
    name: string
    version: string
  }
  phase_percentages: {
    g1: number
    s: number
    g2_m: number
  }
  fit_metrics: FitMetrics
  parameters: FitParameters
  series: FitSeries
  warnings: string[]
  quality_flags: QualityFlag[]
}

export type SourceMode = 'demo' | 'upload'

export type ParameterMode = 'auto' | 'manual'

export type VisibleSeries = {
  observed: boolean
  fit_total: boolean
  g1: boolean
  s: boolean
  g2_m: boolean
}
