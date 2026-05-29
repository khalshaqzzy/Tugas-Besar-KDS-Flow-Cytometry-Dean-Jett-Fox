import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import type { FitResponse } from './types'

const datasets = [
  {
    id: 'zenodo-14928071-ai-0',
    name: 'Zenodo 14928071 AI 0h PI-A',
    source_file: 'Specimen_001_AI_0_001.fcs',
    condition: 'AI',
    timepoint_hours: '0',
    channel: 'PI-A',
    events_total: 54449,
    events_used: 54206,
    bin_count: 256,
    csv_path: 'data/processed/demo.csv',
  },
]

const fitResponse: FitResponse = {
  fit_id: 'zenodo-14928071-ai-0-default',
  model_info: { name: 'dean-jett-fox', version: 'djf_polynomial_broadened_v2' },
  phase_percentages: { g1: 60, s: 30, g2_m: 10 },
  fit_metrics: {
    sse: 1,
    rmse: 2.4,
    r_squared: 0.91,
    weighted_sse: 55,
    reduced_chi_square: 1.4,
  },
  parameters: {
    g1_mean: 20,
    g1_sigma: 3,
    g2_mean: 40,
    g2_sigma: 4,
    g1_mean_scaled: 0.2,
    g2_mean_scaled: 0.4,
    g1_sigma_scaled: 0.03,
    g2_sigma_scaled: 0.04,
    s_polynomial_coefficients: [1, 1, 1],
    g2_g1_ratio: 2,
    g1_cv: 0.15,
    debris_area: 3,
    debris_percent_of_total_signal: 2.5,
  },
  series: {
    bins: [10, 20, 30],
    observed: [1, 4, 2],
    fit_total: [1.1, 3.8, 2.1],
    g1: [0.8, 2.1, 0.3],
    s: [0.1, 0.9, 1.0],
    s_unbroadened: [0.1, 0.8, 0.9],
    g2_m: [0.1, 0.8, 0.8],
    residual: [-0.1, 0.2, -0.1],
    weighted_residual: [-0.1, 0.1, -0.1],
    debris: [0, 0, 0],
    background: [0, 0, 0],
  },
  warnings: ['Reduced chi-square tinggi; residual berbobot masih besar.'],
  quality_flags: [
    {
      key: 'high-reduced-chi-square',
      severity: 'warning',
      label: 'High reduced chi-square',
      message: 'Weighted residuals remain large; review the residual chart before interpreting phase estimates.',
    },
  ],
}

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/health')) {
        return Promise.resolve(jsonResponse({ status: 'ok', service: 'djf-flow-cytometry-api', model: 'dean-jett-fox' }))
      }
      if (url.endsWith('/datasets')) {
        return Promise.resolve(jsonResponse({ datasets }))
      }
      if (url.endsWith('/fit') || url.endsWith('/fit/csv')) {
        return Promise.resolve(jsonResponse(fitResponse))
      }
      return Promise.resolve(jsonResponse({ detail: 'not found' }, 404))
    }),
  )
})

describe('App', () => {
  it('loads demo datasets and renders a successful fit', async () => {
    const user = userEvent.setup()
    render(<App />)

    expect(await screen.findByText('Backend online')).toBeInTheDocument()
    expect(screen.getByText('Data source')).toBeInTheDocument()
    expect(screen.getAllByText('Parameter strategy').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Zenodo 14928071 AI 0h PI-A').length).toBeGreaterThan(0)
    expect(screen.getByText(/Dataset ini berasal dari kondisi AI pada waktu 0 jam/)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /fit dataset/i }))

    expect(await screen.findByText('60%')).toBeInTheDocument()
    expect(screen.getByText('Analisis fitting')).toBeInTheDocument()
    expect(screen.getByText('Gunakan dengan hati-hati')).toBeInTheDocument()
    expect(screen.getByText(/Fitting terakhir menggunakan Zenodo 14928071 AI 0h PI-A/)).toBeInTheDocument()
    expect(screen.getAllByText(/Residual absolut terbesar muncul di sekitar bin 20/).length).toBeGreaterThan(0)
    expect(screen.getByText(/Reduced chi-square tinggi/)).toBeInTheDocument()
  })

  it('switches source mode to CSV upload and previews sample rows', async () => {
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('Backend online')
    await user.click(screen.getByRole('button', { name: /csv upload/i }))
    expect(screen.getByText('Choose histogram CSV')).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Upload histogram CSV'), new File(['bin,count\n1,2\n2,3\n3,4\n'], 'histogram.csv', { type: 'text/csv' }))

    await waitFor(() => expect(screen.getAllByText('histogram.csv').length).toBeGreaterThan(0))
    expect(await screen.findByText('3 rows')).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Bin' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Count' })).toBeInTheDocument()
  })

  it('blocks running when manual parameter order is invalid', async () => {
    const user = userEvent.setup()
    render(<App />)

    await screen.findByText('Backend online')
    expect(screen.getByLabelText('G1 mean value')).toBeDisabled()
    await user.click(screen.getByRole('button', { name: /manual initial means/i }))
    await user.clear(screen.getByLabelText('G1 mean value'))
    await user.type(screen.getByLabelText('G1 mean value'), '50')
    await user.clear(screen.getByLabelText('G2/M mean value'))
    await user.type(screen.getByLabelText('G2/M mean value'), '25')

    expect(screen.getByText(/G2\/M mean harus lebih besar/)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('button', { name: /fit dataset/i })).toBeDisabled())
  })
})
