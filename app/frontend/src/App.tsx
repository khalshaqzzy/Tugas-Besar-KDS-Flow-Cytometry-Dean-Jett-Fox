import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  ChartLine,
  CheckCircle,
  Database,
  Flask,
  Pulse,
  SlidersHorizontal,
  UploadSimple,
  WarningCircle,
} from '@phosphor-icons/react'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { fetchDatasets, fetchHealth, fitCsv, fitDataset } from './api'
import {
  boundsFromResult,
  buildFitAnalysis,
  formatNumber,
  initialParametersFromInputs,
  manualParameterError,
  percent,
  previewHistogramCsv,
  type FitAnalysis,
  type FitRunContext,
  type HistogramPreview,
} from './lab-utils'
import type { DatasetSummary, FitResponse, ParameterMode, SourceMode, VisibleSeries } from './types'

const DEFAULT_VISIBLE_SERIES: VisibleSeries = {
  observed: true,
  fit_total: true,
  g1: true,
  s: true,
  g2_m: true,
}

const SERIES_LABELS: Record<keyof VisibleSeries, string> = {
  observed: 'Observed',
  fit_total: 'Fit total',
  g1: 'G1',
  s: 'S',
  g2_m: 'G2/M',
}

const SERIES_COLORS: Record<keyof VisibleSeries, string> = {
  observed: '#cbd5e1',
  fit_total: '#18181b',
  g1: '#475569',
  s: '#0f766e',
  g2_m: '#b45309',
}

function App() {
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>('checking')
  const [datasets, setDatasets] = useState<DatasetSummary[]>([])
  const [datasetsError, setDatasetsError] = useState<string | null>(null)
  const [sourceMode, setSourceMode] = useState<SourceMode>('demo')
  const [parameterMode, setParameterMode] = useState<ParameterMode>('auto')
  const [datasetId, setDatasetId] = useState('')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadPreview, setUploadPreview] = useState<HistogramPreview | null>(null)
  const [uploadPreviewNote, setUploadPreviewNote] = useState<string | null>(null)
  const [g1Mean, setG1Mean] = useState('')
  const [g2Mean, setG2Mean] = useState('')
  const [result, setResult] = useState<FitResponse | null>(null)
  const [lastFitContext, setLastFitContext] = useState<FitRunContext | null>(null)
  const [fitError, setFitError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [visibleSeries, setVisibleSeries] = useState<VisibleSeries>(DEFAULT_VISIBLE_SERIES)

  const loadBackendState = async () => {
    setHealth('checking')
    setDatasetsError(null)
    try {
      await fetchHealth()
      setHealth('online')
      const nextDatasets = await fetchDatasets()
      setDatasets(nextDatasets)
      setDatasetId((current) => current || nextDatasets[0]?.id || '')
    } catch (error) {
      setHealth('offline')
      setDatasetsError(error instanceof Error ? error.message : 'Backend tidak dapat dijangkau.')
    }
  }

  useEffect(() => {
    void loadBackendState()
  }, [])

  const selectedDataset = datasets.find((dataset) => dataset.id === datasetId)
  const resultBounds = boundsFromResult(result)
  const activeBounds =
    sourceMode === 'upload'
      ? uploadPreview ?? resultBounds ?? { rows: 0, minBin: 0, maxBin: 100000, totalCount: 0, maxCount: 0, sampleRows: [] }
      : resultBounds ?? { rows: 0, minBin: 0, maxBin: 100000, totalCount: 0, maxCount: 0, sampleRows: [] }
  const sliderStep = Math.max((activeBounds.maxBin - activeBounds.minBin) / 250, 1)
  const manualEnabled = parameterMode === 'manual'
  const parameterError = manualParameterError(manualEnabled, g1Mean, g2Mean)
  const canRun =
    !loading &&
    health === 'online' &&
    (sourceMode === 'demo' ? datasetId !== '' : uploadedFile !== null) &&
    parameterError === null

  const chartData = useMemo(() => {
    if (!result) {
      return []
    }
    return result.series.bins.map((bin, index) => ({
      bin,
      observed: result.series.observed[index],
      fit_total: result.series.fit_total[index],
      g1: result.series.g1[index],
      s: result.series.s[index],
      g2_m: result.series.g2_m[index],
      residual: result.series.residual[index],
    }))
  }, [result])

  const sourceLabel =
    sourceMode === 'demo'
      ? selectedDataset?.name ?? 'No dataset selected'
      : uploadedFile?.name ?? 'No CSV selected'
  const parameterLabel = parameterMode === 'manual' ? 'Manual G1/G2' : 'Auto-estimated'
  const fitAnalysis = result && lastFitContext ? buildFitAnalysis(result, lastFitContext) : null

  function switchSourceMode(nextMode: SourceMode) {
    setSourceMode(nextMode)
    setParameterMode('auto')
    setG1Mean('')
    setG2Mean('')
  }

  function switchParameterMode(nextMode: ParameterMode) {
    setParameterMode(nextMode)
    if (nextMode === 'manual' && (!g1Mean || !g2Mean)) {
      if (result) {
        setG1Mean(String(Math.round(result.parameters.g1_mean)))
        setG2Mean(String(Math.round(result.parameters.g2_mean)))
      } else {
        const span = activeBounds.maxBin - activeBounds.minBin
        setG1Mean(String(Math.round(activeBounds.minBin + span * 0.34)))
        setG2Mean(String(Math.round(activeBounds.minBin + span * 0.68)))
      }
    }
  }

  async function handleUpload(file: File | null) {
    setUploadedFile(file)
    setUploadPreview(null)
    setUploadPreviewNote(null)
    if (!file) {
      return
    }
    try {
      const preview = previewHistogramCsv(await file.text())
      if (preview) {
        setUploadPreview(preview)
      } else {
        setUploadPreviewNote('Preview unavailable; backend will validate the CSV on run.')
      }
    } catch {
      setUploadPreviewNote('Preview unavailable; backend will validate the CSV on run.')
    }
  }

  async function runFit() {
    if (!canRun) {
      return
    }
    setLoading(true)
    setFitError(null)
    const initialParameters = initialParametersFromInputs(manualEnabled, g1Mean, g2Mean)
    const runContext: FitRunContext = {
      sourceMode,
      parameterMode,
      sourceLabel,
      dataset: selectedDataset,
      fileName: uploadedFile?.name,
    }
    try {
      const nextResult =
        sourceMode === 'demo'
          ? await fitDataset(datasetId, initialParameters)
          : await fitCsv(uploadedFile as File, initialParameters)
      setResult(nextResult)
      setLastFitContext(runContext)
    } catch (error) {
      setFitError(error instanceof Error ? error.message : 'Fitting gagal dijalankan.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-[100dvh] w-full overflow-x-hidden bg-lab-bg px-4 py-4 text-lab-ink md:px-6">
      <div className="mx-auto flex max-w-[1500px] flex-col gap-4">
        <header className="lab-surface sticky top-4 z-20 flex flex-col gap-4 rounded-2xl px-4 py-4 lg:flex-row lg:items-center lg:justify-between lg:px-5">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl border border-teal-800/15 bg-teal-50 text-lab-teal">
              <Flask size={22} weight="duotone" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-lab-muted">Dean-Jett-Fox Lab</p>
              <h1 className="text-xl font-semibold tracking-tight md:text-2xl">Cell cycle fitting workspace</h1>
            </div>
          </div>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
            <StatusChip health={health} />
            <TopChip label="Source" value={sourceLabel} />
            <TopChip label="Params" value={parameterLabel} />
            <button
              type="button"
              onClick={() => void runFit()}
              disabled={!canRun}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-lab-teal px-5 py-2.5 text-sm font-semibold text-white shadow-[0_14px_30px_-18px_rgba(15,118,110,0.9)] transition duration-200 active:translate-y-[1px] disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
            >
              <Pulse size={18} />
              {loading ? 'Running fit' : sourceMode === 'demo' ? 'Fit dataset' : 'Fit CSV'}
            </button>
          </div>
        </header>

        <section className="grid min-w-0 gap-4 xl:grid-cols-[340px_minmax(0,1fr)_360px]">
          <aside className="lab-surface min-w-0 rounded-2xl p-4">
            <div className="mb-5 flex items-center justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold tracking-tight">Input setup</h2>
                <p className="text-sm text-lab-muted">{sourceLabel}</p>
              </div>
              <Database className="text-lab-teal" size={22} />
            </div>

            <SegmentedControl
              label="Data source"
              value={sourceMode}
              options={[
                { value: 'demo', label: 'Zenodo dataset' },
                { value: 'upload', label: 'CSV upload' },
              ]}
              onChange={(value) => switchSourceMode(value as SourceMode)}
            />

            {sourceMode === 'demo' ? (
              <DatasetSelector datasets={datasets} datasetId={datasetId} selectedDataset={selectedDataset} onChange={setDatasetId} />
            ) : (
              <CsvUpload uploadedFile={uploadedFile} uploadPreview={uploadPreview} uploadPreviewNote={uploadPreviewNote} onUpload={handleUpload} />
            )}

            <div className="mt-5 border-t border-slate-200 pt-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-base font-semibold tracking-tight">Parameter strategy</h2>
                  <p className="text-sm text-lab-muted">Initial G1/G2 means</p>
                </div>
                <SlidersHorizontal className="text-lab-teal" size={21} />
              </div>
              <SegmentedControl
                label="Parameter strategy"
                value={parameterMode}
                options={[
                  { value: 'auto', label: 'Auto-estimated' },
                  { value: 'manual', label: 'Manual initial means' },
                ]}
                onChange={(value) => switchParameterMode(value as ParameterMode)}
              />
              <div className="mt-4">
                <ParameterControl
                  id="g1-mean"
                  label="G1 mean"
                  disabled={!manualEnabled}
                  value={g1Mean}
                  min={activeBounds.minBin}
                  max={activeBounds.maxBin}
                  step={sliderStep}
                  onChange={setG1Mean}
                />
                <ParameterControl
                  id="g2-mean"
                  label="G2/M mean"
                  disabled={!manualEnabled}
                  value={g2Mean}
                  min={activeBounds.minBin}
                  max={activeBounds.maxBin}
                  step={sliderStep}
                  onChange={setG2Mean}
                />
                {parameterError ? <p className="mt-3 rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-800">{parameterError}</p> : null}
              </div>
            </div>
          </aside>

          <section className="lab-surface min-w-0 rounded-2xl p-4 md:min-h-[680px] md:p-5">
            <div className="mb-4 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-lab-muted">Analysis canvas</p>
                <h2 className="text-2xl font-semibold tracking-tight">Histogram fit and residuals</h2>
                {fitAnalysis ? <p className="mt-2 max-w-xl text-sm text-lab-muted">{fitAnalysis.visualRead}</p> : null}
              </div>
              <div className="flex flex-wrap gap-2">
                {(Object.keys(SERIES_LABELS) as Array<keyof VisibleSeries>).map((key) => (
                  <label
                    key={key}
                    className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-lab-muted"
                  >
                    <input
                      type="checkbox"
                      checked={visibleSeries[key]}
                      onChange={() => setVisibleSeries((current) => ({ ...current, [key]: !current[key] }))}
                      className="size-3 accent-teal-700"
                    />
                    <span className="size-2 rounded-full" style={{ background: SERIES_COLORS[key] }} />
                    {SERIES_LABELS[key]}
                  </label>
                ))}
              </div>
            </div>

            {loading ? <ChartSkeleton /> : result ? <FitCharts data={chartData} result={result} visibleSeries={visibleSeries} /> : <EmptyCanvas />}
          </section>

          <aside className="flex min-w-0 flex-col gap-4">
            <section className="lab-surface rounded-2xl p-4">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-base font-semibold tracking-tight">Fit summary</h2>
                {result ? <CheckCircle size={21} className="text-lab-teal" /> : <ChartLine size={21} className="text-lab-muted" />}
              </div>
              {result ? <FitSummary result={result} /> : <p className="text-sm text-lab-muted">Run a dataset or uploaded CSV to populate phase percentages and model metrics.</p>}
            </section>

            {result && fitAnalysis ? <FitAnalysisPanel analysis={fitAnalysis} result={result} /> : null}

            <section className="lab-surface rounded-2xl p-4">
              <div className="mb-3 flex items-center gap-2">
                <WarningCircle size={20} className={result?.warnings.length ? 'text-amber-700' : 'text-lab-muted'} />
                <h2 className="text-base font-semibold tracking-tight">Warnings and caveats</h2>
              </div>
              {fitError ? (
                <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">{fitError}</div>
              ) : null}
              {datasetsError ? (
                <div className="mt-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
                  {datasetsError}
                  <button type="button" onClick={() => void loadBackendState()} className="mt-2 block font-semibold text-rose-900 underline">
                    Retry connection
                  </button>
                </div>
              ) : null}
              {result?.warnings.length ? (
                <ul className="space-y-2 text-sm text-amber-800">
                  {result.warnings.map((warning) => (
                    <li key={warning} className="rounded-xl bg-amber-50 px-3 py-2">
                      {warning}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-lab-muted">Peringatan model akan muncul di sini ketika fitting berhasil tetapi masih memiliki catatan kualitas.</p>
              )}
              <p className="mt-4 border-t border-slate-200 pt-4 text-xs leading-5 text-lab-muted">
                Keluaran ini adalah estimasi komputasi dari fitting histogram PI-A, bukan ground truth klinis. Interpretasi perlu mempertimbangkan gating, debris, dan kualitas residual.
              </p>
            </section>
          </aside>
        </section>
      </div>
    </main>
  )
}

function StatusChip({ health }: { health: 'checking' | 'online' | 'offline' }) {
  return (
    <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm text-lab-muted">
      <span className={`size-2 rounded-full ${health === 'online' ? 'bg-teal-600' : health === 'checking' ? 'bg-amber-500' : 'bg-rose-500'}`} />
      <span>{health === 'online' ? 'Backend online' : health === 'checking' ? 'Checking backend' : 'Backend offline'}</span>
    </div>
  )
}

function TopChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs text-lab-muted lg:max-w-56">
      <span className="font-semibold text-lab-ink">{label}: </span>
      <span className="truncate align-bottom">{value}</span>
    </div>
  )
}

function SegmentedControl({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: Array<{ value: string; label: string }>
  onChange: (value: string) => void
}) {
  return (
    <div className="mb-5">
      <p className="mb-2 text-sm font-medium text-lab-muted">{label}</p>
      <div className="grid grid-cols-2 rounded-xl border border-slate-200 bg-slate-50 p-1 text-sm font-medium">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`rounded-lg px-3 py-2 transition active:scale-[0.98] ${value === option.value ? 'bg-white text-lab-ink shadow-sm' : 'text-lab-muted'}`}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}

function DatasetSelector({
  datasets,
  datasetId,
  selectedDataset,
  onChange,
}: {
  datasets: DatasetSummary[]
  datasetId: string
  selectedDataset?: DatasetSummary
  onChange: (value: string) => void
}) {
  return (
    <div className="mb-5">
      <label className="block">
        <span className="mb-2 block text-sm font-medium text-lab-muted">Dataset</span>
        <select
          value={datasetId}
          onChange={(event) => onChange(event.target.value)}
          className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-lab-ink"
        >
          {datasets.map((dataset) => (
            <option key={dataset.id} value={dataset.id}>
              {dataset.name}
            </option>
          ))}
        </select>
      </label>
      {selectedDataset ? <DatasetDescription dataset={selectedDataset} /> : null}
    </div>
  )
}

function DatasetDescription({ dataset }: { dataset: DatasetSummary }) {
  const items = [
    ['Kondisi', dataset.condition],
    ['Waktu', `${dataset.timepoint_hours} jam`],
    ['Channel', dataset.channel],
    ['Event', `${formatNumber(dataset.events_used, 0)} / ${formatNumber(dataset.events_total, 0)}`],
    ['Bins', formatNumber(dataset.bin_count, 0)],
    ['File sumber', dataset.source_file],
  ]
  return (
    <div className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-3">
      <p className="text-sm leading-5 text-lab-ink">
        Dataset ini berasal dari kondisi {dataset.condition} pada waktu {dataset.timepoint_hours} jam. Sinyal diukur pada channel {dataset.channel}, lalu diproses menjadi histogram konten DNA dengan {dataset.bin_count} bin untuk fitting Dean-Jett-Fox.
      </p>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
        {items.map(([label, value]) => (
          <div key={label} className={label === 'File sumber' ? 'col-span-2' : undefined}>
            <dt className="text-lab-muted">{label}</dt>
            <dd className="mt-0.5 truncate font-medium text-lab-ink">{value}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 truncate border-t border-slate-200 pt-2 font-mono text-[11px] text-lab-muted">{dataset.csv_path}</p>
    </div>
  )
}

function CsvUpload({
  uploadedFile,
  uploadPreview,
  uploadPreviewNote,
  onUpload,
}: {
  uploadedFile: File | null
  uploadPreview: HistogramPreview | null
  uploadPreviewNote: string | null
  onUpload: (file: File | null) => void
}) {
  return (
    <div className="mb-5">
      <label className="flex min-h-32 cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-center transition hover:border-teal-700/50 hover:bg-teal-50/40">
        <UploadSimple size={24} className="mb-3 text-lab-teal" />
        <span className="text-sm font-semibold text-lab-ink">{uploadedFile?.name ?? 'Choose histogram CSV'}</span>
        <span className="mt-1 text-xs text-lab-muted">Headers: bin,count or two numeric columns</span>
        <input
          aria-label="Upload histogram CSV"
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          onChange={(event) => void onUpload(event.target.files?.[0] ?? null)}
        />
      </label>
      {uploadPreview ? <CsvPreviewTable preview={uploadPreview} /> : null}
      {uploadPreviewNote ? <p className="mt-2 rounded-xl bg-amber-50 px-3 py-2 text-xs text-amber-800">{uploadPreviewNote}</p> : null}
    </div>
  )
}

function CsvPreviewTable({ preview }: { preview: HistogramPreview }) {
  return (
    <div className="mt-3 rounded-2xl border border-slate-200 bg-white">
      <div className="grid grid-cols-2 gap-2 border-b border-slate-200 p-3 text-xs text-lab-muted">
        <span>{preview.rows} rows</span>
        <span className="text-right">Max count {formatNumber(preview.maxCount, 0)}</span>
        <span>Bins {formatNumber(preview.minBin, 0)} to {formatNumber(preview.maxBin, 0)}</span>
        <span className="text-right">Total {formatNumber(preview.totalCount, 0)}</span>
      </div>
      <div className="max-h-56 overflow-auto">
        <table className="w-full border-collapse text-left text-xs">
          <thead className="sticky top-0 bg-slate-50 text-lab-muted">
            <tr>
              <th className="border-b border-slate-200 px-3 py-2 font-medium">Bin</th>
              <th className="border-b border-slate-200 px-3 py-2 text-right font-medium">Count</th>
            </tr>
          </thead>
          <tbody className="font-mono">
            {preview.sampleRows.map((row, index) => (
              <tr key={`${row.bin}-${index}`} className="border-b border-slate-100 last:border-0">
                <td className="px-3 py-2">{formatNumber(row.bin, 3)}</td>
                <td className="px-3 py-2 text-right">{formatNumber(row.count, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ParameterControl({
  id,
  label,
  disabled,
  value,
  min,
  max,
  step,
  onChange,
}: {
  id: string
  label: string
  disabled: boolean
  value: string
  min: number
  max: number
  step: number
  onChange: (value: string) => void
}) {
  const sliderValue = value === '' || !Number.isFinite(Number(value)) ? min : Number(value)
  return (
    <div className="mb-4 grid gap-2">
      <label htmlFor={id} className="text-sm font-medium text-lab-muted">
        {label}
      </label>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        value={Math.min(Math.max(sliderValue, min), max)}
        onChange={(event) => onChange(event.target.value)}
        className="w-full accent-teal-700 disabled:opacity-40"
      />
      <input
        aria-label={`${label} value`}
        type="number"
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm disabled:bg-slate-100 disabled:text-slate-400"
      />
    </div>
  )
}

function EmptyCanvas() {
  return (
    <div className="grid min-h-[560px] place-items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50/70">
      <div className="max-w-sm text-center">
        <ChartLine size={34} className="mx-auto mb-4 text-lab-teal" />
        <h3 className="text-lg font-semibold tracking-tight">Siap menjalankan fitting</h3>
        <p className="mt-2 text-sm leading-6 text-lab-muted">
          Pilih sumber data, tentukan strategi parameter awal otomatis atau manual, lalu jalankan fitting histogram.
        </p>
      </div>
    </div>
  )
}

function ChartSkeleton() {
  return (
    <div className="grid gap-4">
      <div className="skeleton h-[420px] rounded-2xl" />
      <div className="skeleton h-[170px] rounded-2xl" />
    </div>
  )
}

function FitCharts({ data, result, visibleSeries }: { data: Array<Record<string, number>>; result: FitResponse; visibleSeries: VisibleSeries }) {
  return (
    <div className="grid gap-4">
      <ChartFrame heightClass="h-[420px]">
        {(width, height) => (
          <ComposedChart width={width} height={height} data={data} margin={{ top: 18, right: 18, left: 8, bottom: 8 }}>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
            <XAxis dataKey="bin" type="number" domain={['dataMin', 'dataMax']} tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} minTickGap={28} />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} width={52} />
            <Tooltip contentStyle={{ borderRadius: 14, borderColor: '#e2e8f0' }} />
            <ReferenceLine x={result.parameters.g1_mean} stroke="#475569" strokeDasharray="4 4" label={{ value: 'G1', fontSize: 11, fill: '#475569' }} />
            <ReferenceLine x={result.parameters.g2_mean} stroke="#b45309" strokeDasharray="4 4" label={{ value: 'G2/M', fontSize: 11, fill: '#b45309' }} />
            {visibleSeries.observed ? <Bar dataKey="observed" fill={SERIES_COLORS.observed} opacity={0.72} name="Observed" /> : null}
            {visibleSeries.fit_total ? <Line type="monotone" dataKey="fit_total" stroke={SERIES_COLORS.fit_total} strokeWidth={2.2} dot={false} name="Fit total" /> : null}
            {visibleSeries.g1 ? <Line type="monotone" dataKey="g1" stroke={SERIES_COLORS.g1} strokeWidth={1.8} dot={false} name="G1" /> : null}
            {visibleSeries.s ? <Line type="monotone" dataKey="s" stroke={SERIES_COLORS.s} strokeWidth={1.8} dot={false} name="S" /> : null}
            {visibleSeries.g2_m ? <Line type="monotone" dataKey="g2_m" stroke={SERIES_COLORS.g2_m} strokeWidth={1.8} dot={false} name="G2/M" /> : null}
          </ComposedChart>
        )}
      </ChartFrame>
      <ChartFrame heightClass="h-[170px]">
        {(width, height) => (
          <ComposedChart width={width} height={height} data={data} margin={{ top: 12, right: 18, left: 8, bottom: 8 }}>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
            <XAxis dataKey="bin" type="number" domain={['dataMin', 'dataMax']} tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} minTickGap={28} />
            <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} width={52} />
            <Tooltip contentStyle={{ borderRadius: 14, borderColor: '#e2e8f0' }} />
            <ReferenceLine y={0} stroke="#94a3b8" />
            <Line type="monotone" dataKey="residual" stroke="#be123c" strokeWidth={1.7} dot={false} name="Residual" />
          </ComposedChart>
        )}
      </ChartFrame>
    </div>
  )
}

function ChartFrame({
  heightClass,
  children,
}: {
  heightClass: string
  children: (width: number, height: number) => ReactNode
}) {
  const ref = useRef<HTMLDivElement | null>(null)
  const [size, setSize] = useState({ width: 0, height: 0 })

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const updateSize = () => {
      const rect = element.getBoundingClientRect()
      setSize({ width: Math.floor(rect.width), height: Math.floor(rect.height) })
    }

    updateSize()
    const observer = new ResizeObserver(updateSize)
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  const hasSize = size.width > 0 && size.height > 0
  return (
    <div className={`${heightClass} rounded-2xl border border-slate-200 bg-white p-3`}>
      <div ref={ref} className="h-full min-h-0 w-full min-w-0">
        {hasSize ? children(size.width, size.height) : null}
      </div>
    </div>
  )
}

function FitSummary({ result }: { result: FitResponse }) {
  const phases = [
    { key: 'g1', label: 'G1', value: result.phase_percentages.g1, color: '#475569' },
    { key: 's', label: 'S', value: result.phase_percentages.s, color: '#0f766e' },
    { key: 'g2_m', label: 'G2/M', value: result.phase_percentages.g2_m, color: '#b45309' },
  ]
  return (
    <div>
      <div className="mb-4 grid grid-cols-3 gap-2">
        {phases.map((phase) => (
          <div key={phase.key} className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3">
            <p className="text-xs font-semibold text-lab-muted">{phase.label}</p>
            <p className="mt-1 text-lg font-semibold tracking-tight">{percent(phase.value)}</p>
          </div>
        ))}
      </div>
      <div className="mb-5 flex h-3 overflow-hidden rounded-full bg-slate-100">
        {phases.map((phase) => (
          <span key={phase.key} style={{ width: `${phase.value}%`, background: phase.color }} />
        ))}
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <Metric label="RMSE" value={formatNumber(result.fit_metrics.rmse, 2)} />
        <Metric label="R-squared" value={formatNumber(result.fit_metrics.r_squared, 3)} />
        <Metric label="Reduced chi-square" value={formatNumber(result.fit_metrics.reduced_chi_square, 2)} />
        <Metric label="Weighted SSE" value={formatNumber(result.fit_metrics.weighted_sse, 0)} />
        <Metric label="G2/G1 ratio" value={formatNumber(result.parameters.g2_g1_ratio, 3)} />
        <Metric label="Debris signal" value={percent(result.parameters.debris_percent_of_total_signal)} />
      </dl>
      <p className="mt-4 rounded-xl bg-slate-50 px-3 py-2 text-xs text-lab-muted">Model: {result.model_info.version}</p>
    </div>
  )
}

function FitAnalysisPanel({ analysis, result }: { analysis: FitAnalysis; result: FitResponse }) {
  const qualityText = analysis.qualityLabel === 'Good fit' ? 'Fit baik' : analysis.qualityLabel === 'Review fit' ? 'Perlu ditinjau' : 'Gunakan dengan hati-hati'
  return (
    <section className="lab-surface rounded-2xl p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold tracking-tight">Analisis fitting</h2>
          <p className="text-sm text-lab-muted">{qualityText}</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${analysis.qualityLabel === 'Good fit' ? 'bg-teal-50 text-teal-800' : analysis.qualityLabel === 'Review fit' ? 'bg-amber-50 text-amber-800' : 'bg-rose-50 text-rose-800'}`}>
          {analysis.dominantPhase}
        </span>
      </div>
      <div className="space-y-3 text-sm leading-6 text-lab-muted">
        <p>{analysis.phaseInterpretation}</p>
        <p>{analysis.fitQuality}</p>
        <p>{analysis.visualRead}</p>
        <p className="rounded-xl bg-slate-50 px-3 py-2 text-xs">{analysis.provenance}</p>
      </div>
      <div className="mt-4 space-y-2 border-t border-slate-200 pt-4">
        {result.quality_flags.map((flag) => (
          <div key={`${flag.key}-${flag.label}`} className="rounded-xl bg-slate-50 px-3 py-2">
            <p className="text-xs font-semibold text-lab-ink">{flag.label}</p>
            <p className="mt-1 text-xs leading-5 text-lab-muted">{flag.message}</p>
          </div>
        ))}
      </div>
    </section>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-lab-muted">{label}</dt>
      <dd className="mt-0.5 font-semibold text-lab-ink">{value}</dd>
    </div>
  )
}

export default App
