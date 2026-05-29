import { describe, expect, it } from 'vitest'
import { buildFitAnalysis, manualParameterError, previewHistogramCsv } from './lab-utils'
import type { FitResponse } from './types'

describe('lab utilities', () => {
  it('previews supported CSV formats', () => {
    expect(previewHistogramCsv('bin,count\n10,4\n20,8\n30,5\n')).toEqual({
      rows: 3,
      minBin: 10,
      maxBin: 30,
      totalCount: 17,
      maxCount: 8,
      sampleRows: [
        { bin: 10, count: 4 },
        { bin: 20, count: 8 },
        { bin: 30, count: 5 },
      ],
    })
    expect(previewHistogramCsv('10,4\n20,8\n30,5\n')).toEqual({
      rows: 3,
      minBin: 10,
      maxBin: 30,
      totalCount: 17,
      maxCount: 8,
      sampleRows: [
        { bin: 10, count: 4 },
        { bin: 20, count: 8 },
        { bin: 30, count: 5 },
      ],
    })
  })

  it('rejects preview when values are malformed', () => {
    expect(previewHistogramCsv('bin,count\n10,4\n20,nope\n30,5\n')).toBeNull()
    expect(previewHistogramCsv('bin,count\n10,4\n')).toBeNull()
  })

  it('validates manual parameter ordering', () => {
    expect(manualParameterError(false, '', '')).toBeNull()
    expect(manualParameterError(true, '', '')).toContain('G1')
    expect(manualParameterError(true, '20', '10')).toContain('G2/M')
    expect(manualParameterError(true, '10', '20')).toBeNull()
  })

  it('builds cautious fit analysis from metrics and residuals', () => {
    const result: FitResponse = {
      fit_id: 'fit-1',
      model_info: { name: 'dean-jett-fox', version: 'test' },
      phase_percentages: { g1: 20, s: 65, g2_m: 15 },
      fit_metrics: { sse: 1, rmse: 1, r_squared: 0.72, weighted_sse: 1, reduced_chi_square: 31 },
      parameters: {
        g1_mean: 10,
        g1_sigma: 1,
        g2_mean: 20,
        g2_sigma: 1,
        g1_mean_scaled: 0.1,
        g2_mean_scaled: 0.2,
        g1_sigma_scaled: 0.01,
        g2_sigma_scaled: 0.01,
        s_polynomial_coefficients: [1, 1, 1],
        g2_g1_ratio: 2,
        g1_cv: 0.1,
        debris_area: 1,
        debris_percent_of_total_signal: 2,
      },
      series: {
        bins: [10, 20, 30],
        observed: [1, 2, 3],
        fit_total: [1, 2, 3],
        g1: [1, 1, 0],
        s: [0, 1, 2],
        s_unbroadened: [0, 1, 2],
        g2_m: [0, 0, 1],
        residual: [0.2, -4.5, 1],
        weighted_residual: [0.2, -4.5, 1],
        debris: [0, 0, 0],
        background: [0, 0, 0],
      },
      warnings: [],
      quality_flags: [{ key: 'low-r-squared', severity: 'warning', label: 'R-squared rendah', message: 'Tinjau fitting.' }],
    }

    const analysis = buildFitAnalysis(result, {
      sourceMode: 'upload',
      parameterMode: 'auto',
      sourceLabel: 'sample.csv',
      fileName: 'sample.csv',
    })

    expect(analysis.qualityLabel).toBe('Use with caution')
    expect(analysis.dominantPhase).toBe('fase S')
    expect(analysis.largestResidual).toEqual({ bin: 20, value: -4.5 })
    expect(analysis.provenance).toContain('sample.csv')
  })
})
