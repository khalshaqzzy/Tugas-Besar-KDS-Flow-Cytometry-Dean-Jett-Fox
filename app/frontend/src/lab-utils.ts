import type { DatasetSummary, FitResponse, InitialParameters, ParameterMode, SourceMode } from './types'

export type HistogramPreviewRow = {
  bin: number
  count: number
}

export type HistogramPreview = {
  rows: number
  minBin: number
  maxBin: number
  totalCount: number
  maxCount: number
  sampleRows: HistogramPreviewRow[]
}

export type FitRunContext = {
  sourceMode: SourceMode
  parameterMode: ParameterMode
  sourceLabel: string
  dataset?: DatasetSummary | null
  fileName?: string | null
}

export type FitAnalysis = {
  qualityLabel: 'Good fit' | 'Review fit' | 'Use with caution'
  dominantPhase: string
  phaseInterpretation: string
  fitQuality: string
  visualRead: string
  provenance: string
  largestResidual: {
    bin: number
    value: number
  } | null
}

const HEADER_ALIASES = new Set(['bin,count', 'bins,counts'])

function isNumeric(value: string): boolean {
  return value.trim() !== '' && Number.isFinite(Number(value))
}

export function previewHistogramCsv(text: string): HistogramPreview | null {
  const rows = text
    .split(/\r?\n/)
    .map((line) => line.split(',').map((cell) => cell.trim()))
    .filter((row) => row.some((cell) => cell !== ''))

  if (rows.length === 0) {
    return null
  }

  const firstTwo = rows[0].slice(0, 2).map((cell) => cell.toLowerCase()).join(',')
  const dataRows = HEADER_ALIASES.has(firstTwo) ? rows.slice(1) : rows
  const parsedRows: HistogramPreviewRow[] = []

  for (const row of dataRows) {
    const nonEmpty = row.filter((cell) => cell !== '')
    if (nonEmpty.length !== 2 || !isNumeric(nonEmpty[0]) || !isNumeric(nonEmpty[1])) {
      return null
    }
    const count = Number(nonEmpty[1])
    if (count < 0) {
      return null
    }
    parsedRows.push({ bin: Number(nonEmpty[0]), count })
  }

  if (parsedRows.length < 3) {
    return null
  }

  const bins = parsedRows.map((row) => row.bin)
  const counts = parsedRows.map((row) => row.count)

  return {
    rows: parsedRows.length,
    minBin: Math.min(...bins),
    maxBin: Math.max(...bins),
    totalCount: counts.reduce((total, count) => total + count, 0),
    maxCount: Math.max(...counts),
    sampleRows: parsedRows.slice(0, 12),
  }
}

export function manualParameterError(
  enabled: boolean,
  g1Mean: string,
  g2Mean: string,
): string | null {
  if (!enabled) {
    return null
  }
  const g1 = Number(g1Mean)
  const g2 = Number(g2Mean)
  if (!Number.isFinite(g1) || !Number.isFinite(g2)) {
    return 'Isi nilai G1 dan G2/M terlebih dahulu.'
  }
  if (g2 <= g1) {
    return 'G2/M mean harus lebih besar dari G1 mean.'
  }
  return null
}

export function initialParametersFromInputs(enabled: boolean, g1Mean: string, g2Mean: string): InitialParameters | undefined {
  if (!enabled) {
    return undefined
  }
  return {
    g1_mean: Number(g1Mean),
    g2_mean: Number(g2Mean),
  }
}

export function boundsFromResult(result: FitResponse | null): HistogramPreview | null {
  if (!result || result.series.bins.length === 0) {
    return null
  }
  return {
    rows: result.series.bins.length,
    minBin: Math.min(...result.series.bins),
    maxBin: Math.max(...result.series.bins),
    totalCount: result.series.observed.reduce((total, count) => total + count, 0),
    maxCount: Math.max(...result.series.observed),
    sampleRows: result.series.bins.slice(0, 12).map((bin, index) => ({
      bin,
      count: result.series.observed[index],
    })),
  }
}

function phaseLabel(key: string): string {
  if (key === 'g1') return 'G1'
  if (key === 's') return 'fase S'
  return 'G2/M'
}

function maxAbsoluteResidual(result: FitResponse): FitAnalysis['largestResidual'] {
  if (result.series.residual.length === 0) {
    return null
  }
  let maxIndex = 0
  for (let index = 1; index < result.series.residual.length; index += 1) {
    if (Math.abs(result.series.residual[index]) > Math.abs(result.series.residual[maxIndex])) {
      maxIndex = index
    }
  }
  return {
    bin: result.series.bins[maxIndex],
    value: result.series.residual[maxIndex],
  }
}

export function buildFitAnalysis(result: FitResponse, context: FitRunContext): FitAnalysis {
  const warningFlags = result.quality_flags.filter((flag) => flag.severity === 'warning').length
  const cautionFlags = result.quality_flags.filter((flag) => flag.severity === 'caution').length
  const qualityLabel =
    warningFlags > 0 ? 'Use with caution' : cautionFlags > 0 || result.warnings.length > 0 ? 'Review fit' : 'Good fit'

  const phases = Object.entries(result.phase_percentages).sort((left, right) => right[1] - left[1])
  const [dominantKey, dominantValue] = phases[0] ?? ['g1', 0]
  const dominantPhase = phaseLabel(dominantKey)
  const largestResidual = maxAbsoluteResidual(result)
  const sourceDescription =
    context.sourceMode === 'demo' && context.dataset
      ? `${context.dataset.name} (${context.dataset.source_file})`
      : context.fileName ?? context.sourceLabel
  const parameterDescription =
    context.parameterMode === 'manual'
      ? `parameter awal manual dengan mean G1 sekitar ${formatNumber(result.parameters.g1_mean, 0)} dan mean G2/M sekitar ${formatNumber(result.parameters.g2_mean, 0)}`
      : 'parameter awal otomatis dari backend'

  return {
    qualityLabel,
    dominantPhase,
    phaseInterpretation: `${dominantPhase} menjadi kompartemen estimasi terbesar dengan proporsi ${percent(dominantValue)}. Estimasi fase S adalah ${percent(result.phase_percentages.s)}, sedangkan G2/M adalah ${percent(result.phase_percentages.g2_m)}.`,
    fitQuality: `Kualitas fitting dibaca dari R-squared ${formatNumber(result.fit_metrics.r_squared, 3)} dan reduced chi-square ${formatNumber(result.fit_metrics.reduced_chi_square, 2)}. Model menghasilkan ${result.warnings.length} peringatan yang perlu dipertimbangkan bersama grafik residual.`,
    visualRead: largestResidual
      ? `Residual absolut terbesar muncul di sekitar bin ${formatNumber(largestResidual.bin, 0)} dengan residual bertanda ${formatNumber(largestResidual.value, 1)}. Area ini sebaiknya dibandingkan dengan kurva fit sebelum menarik interpretasi fase.`
      : 'Deret residual tidak tersedia untuk fitting ini.',
    provenance: `Fitting terakhir menggunakan ${sourceDescription} dengan ${parameterDescription}.`,
    largestResidual,
  }
}

export function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value == null || !Number.isFinite(value)) {
    return 'n/a'
  }
  return value.toLocaleString('en-US', {
    maximumFractionDigits: digits,
  })
}

export function percent(value: number): string {
  return `${formatNumber(value, 1)}%`
}
