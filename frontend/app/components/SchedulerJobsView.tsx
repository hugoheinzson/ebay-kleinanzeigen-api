'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  Clock,
  Pause,
  Play,
  RefreshCcw,
  Save,
  Settings,
  Trash2,
  XCircle,
} from 'lucide-react'

import type { SchedulerJob } from '../types'

interface FormState {
  name: string
  query: string
  location: string
  radius: string
  minPrice: string
  maxPrice: string
  pageCount: string
  intervalSeconds: string
  isActive: boolean
}

const defaultFormState: FormState = {
  name: '',
  query: '',
  location: '',
  radius: '',
  minPrice: '',
  maxPrice: '',
  pageCount: '1',
  intervalSeconds: '3600',
  isActive: true,
}

function numberOrNull(value: string): number | null {
  const trimmed = value.trim()
  if (!trimmed) return null
  const numeric = Number(trimmed)
  return Number.isFinite(numeric) ? numeric : null
}

function formatInterval(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) return 'Unbekannt'
  if (seconds < 60) return `${seconds} Sek.`
  const minutes = seconds / 60
  if (minutes < 60) return minutes % 1 === 0 ? `${minutes} Min.` : `${minutes.toFixed(1)} Min.`
  const hours = minutes / 60
  if (hours < 24) return hours % 1 === 0 ? `${hours} Std.` : `${hours.toFixed(1)} Std.`
  const days = hours / 24
  return days % 1 === 0 ? `${days} Tage` : `${days.toFixed(1)} Tage`
}

function formatTimestamp(value?: string | null): string {
  if (!value) return '–'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value
  return parsed.toLocaleString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function jobStatusBadge(job: SchedulerJob): { label: string; className: string } {
  if (job.is_active) {
    return { label: 'Aktiv', className: 'bg-green-100 text-green-700' }
  }
  return { label: 'Pausiert', className: 'bg-gray-100 text-gray-600' }
}

export default function SchedulerJobsView() {
  const [jobs, setJobs] = useState<SchedulerJob[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [formState, setFormState] = useState<FormState>(defaultFormState)
  const [editingJobId, setEditingJobId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [actionMessage, setActionMessage] = useState<string | null>(null)

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/backend/scheduler/jobs')
      if (!response.ok) {
        throw new Error(`Jobs konnten nicht geladen werden (${response.status})`)
      }
      const data = await response.json()
      setJobs(Array.isArray(data.jobs) ? data.jobs : [])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unbekannter Fehler beim Laden'
      setError(message)
      setJobs([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchJobs()
  }, [fetchJobs])

  const resetForm = useCallback(() => {
    setFormState(defaultFormState)
    setEditingJobId(null)
  }, [])

  const handleEdit = useCallback((job: SchedulerJob) => {
    setEditingJobId(job.id)
    setFormState({
      name: job.name,
      query: job.query ?? '',
      location: job.location ?? '',
      radius: job.radius != null ? String(job.radius) : '',
      minPrice: job.min_price != null ? String(job.min_price) : '',
      maxPrice: job.max_price != null ? String(job.max_price) : '',
      pageCount: job.page_count != null ? String(job.page_count) : '1',
      intervalSeconds: job.interval_seconds != null ? String(job.interval_seconds) : '3600',
      isActive: job.is_active,
    })
  }, [])

  const submitForm = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      setSubmitting(true)
      setError(null)
      setActionMessage(null)

      const payloadBase = {
        query: formState.query.trim() || null,
        location: formState.location.trim() || null,
        radius: numberOrNull(formState.radius),
        min_price: numberOrNull(formState.minPrice),
        max_price: numberOrNull(formState.maxPrice),
        page_count: Math.max(1, Number.parseInt(formState.pageCount, 10) || 1),
        interval_seconds: Math.max(60, Number.parseInt(formState.intervalSeconds, 10) || 3600),
        is_active: formState.isActive,
      }

      try {
        if (editingJobId === null) {
          const name = formState.name.trim()
          if (!name) {
            throw new Error('Bitte einen Namen für den Job angeben')
          }
          const response = await fetch('/api/backend/scheduler/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name,
              ...payloadBase,
            }),
          })
          if (!response.ok) {
            const errorText = await response.text()
            throw new Error(errorText || `Erstellen fehlgeschlagen (${response.status})`)
          }
          const data = await response.json()
          setActionMessage(data.message ?? 'Job wurde erstellt')
        } else {
          const response = await fetch(`/api/backend/scheduler/jobs/${editingJobId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payloadBase),
          })
          if (!response.ok) {
            const errorText = await response.text()
            throw new Error(errorText || `Aktualisierung fehlgeschlagen (${response.status})`)
          }
          const data = await response.json()
          setActionMessage(data.message ?? 'Job wurde aktualisiert')
        }

        await fetchJobs()
        resetForm()
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unbekannter Fehler beim Speichern'
        setError(message)
      } finally {
        setSubmitting(false)
      }
    },
    [editingJobId, fetchJobs, formState, resetForm]
  )

  const performJobAction = useCallback(
    async (path: string, method: 'POST' | 'DELETE', successFallback: string) => {
      setError(null)
      setActionMessage(null)
      try {
        const response = await fetch(path, { method })
        if (!response.ok) {
          const errorText = await response.text()
          throw new Error(errorText || `Aktion fehlgeschlagen (${response.status})`)
        }
        const data = await response.json()
        setActionMessage(data.message ?? successFallback)
        await fetchJobs()
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unbekannter Fehler bei der Aktion'
        setError(message)
      }
    },
    [fetchJobs]
  )

  const handleStart = useCallback(
    async (jobId: number) => {
      await performJobAction(`/api/backend/scheduler/jobs/${jobId}/start`, 'POST', 'Job gestartet')
    },
    [performJobAction]
  )

  const handleStop = useCallback(
    async (jobId: number) => {
      await performJobAction(`/api/backend/scheduler/jobs/${jobId}/stop`, 'POST', 'Job gestoppt')
    },
    [performJobAction]
  )

  const handleRunNow = useCallback(
    async (jobId: number) => {
      await performJobAction(`/api/backend/scheduler/jobs/${jobId}/run`, 'POST', 'Job ausgeführt')
    },
    [performJobAction]
  )

  const handleDelete = useCallback(
    async (jobId: number) => {
      await performJobAction(`/api/backend/scheduler/jobs/${jobId}`, 'DELETE', 'Job gelöscht')
      if (editingJobId === jobId) {
        resetForm()
      }
    },
    [editingJobId, performJobAction, resetForm]
  )

  const activeJobs = useMemo(() => jobs.filter((job) => job.is_active).length, [jobs])

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-gray-200 bg-white shadow-sm">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <Settings className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Scheduler Jobs</h2>
              <p className="text-sm text-gray-500">Automatisiere deine Suchläufe und verwalte Intervalle</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              setActionMessage(null)
              void fetchJobs()
            }}
            className="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          >
            <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Aktualisieren
          </button>
        </header>

        <form className="grid gap-4 px-6 py-6 md:grid-cols-2" onSubmit={submitForm}>
          <div className="md:col-span-2">
            <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
              <span>Job-Name</span>
              <input
                type="text"
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                placeholder="z. B. woom-3"
                value={formState.name}
                disabled={editingJobId !== null}
                onChange={(event) =>
                  setFormState((prev) => ({
                    ...prev,
                    name: event.target.value,
                  }))
                }
              />
            </label>
          </div>

          <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
            <span>Suchbegriff</span>
            <input
              type="text"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="z. B. Woom 3"
              value={formState.query}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  query: event.target.value,
                }))
              }
            />
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
            <span>Ort</span>
            <input
              type="text"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="z. B. München"
              value={formState.location}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  location: event.target.value,
                }))
              }
            />
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
            <span>Radius (km)</span>
            <input
              type="number"
              min="0"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="z. B. 25"
              value={formState.radius}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  radius: event.target.value,
                }))
              }
            />
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
            <span>Mindestpreis (€)</span>
            <input
              type="number"
              min="0"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="z. B. 100"
              value={formState.minPrice}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  minPrice: event.target.value,
                }))
              }
            />
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
            <span>Höchstpreis (€)</span>
            <input
              type="number"
              min="0"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="z. B. 400"
              value={formState.maxPrice}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  maxPrice: event.target.value,
                }))
              }
            />
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
            <span>Seiten pro Lauf</span>
            <input
              type="number"
              min="1"
              max="20"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={formState.pageCount}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  pageCount: event.target.value,
                }))
              }
            />
          </label>

          <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
            <span>Intervall (Sekunden)</span>
            <input
              type="number"
              min="60"
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={formState.intervalSeconds}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  intervalSeconds: event.target.value,
                }))
              }
            />
          </label>

          <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <input
              id="job-active-checkbox"
              type="checkbox"
              checked={formState.isActive}
              onChange={(event) =>
                setFormState((prev) => ({
                  ...prev,
                  isActive: event.target.checked,
                }))
              }
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="job-active-checkbox">Job nach dem Speichern aktivieren</label>
          </div>

          <div className="md:col-span-2 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-blue-300"
              disabled={submitting}
            >
              <Save className="h-4 w-4" />
              {editingJobId === null ? 'Job anlegen' : 'Änderungen speichern'}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
            >
              <XCircle className="h-4 w-4" />
              Formular zurücksetzen
            </button>
            {editingJobId !== null && (
              <span className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
                <Settings className="h-4 w-4" />
                Bearbeitung aktiv
              </span>
            )}
          </div>
        </form>
      </section>

      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle className="h-4 w-4" />
          {error}
        </div>
      )}

      {actionMessage && !error && (
        <div className="flex items-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          <CheckCircle2 className="h-4 w-4" />
          {actionMessage}
        </div>
      )}

      <section className="rounded-xl border border-gray-200 bg-white shadow-sm">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-200 px-6 py-4 text-sm text-gray-600">
          <div className="flex items-center gap-3">
            <CalendarClock className="h-5 w-5 text-blue-500" />
            <span>
              {jobs.length} Job{jobs.length === 1 ? '' : 's'} konfiguriert · {activeJobs} aktiv
            </span>
          </div>
        </header>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Job
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Intervall &amp; Umfang
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Zeitpunkte
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Aktionen
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white text-sm text-gray-700">
              {loading && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-500">
                    Lade Scheduler-Jobs...
                  </td>
                </tr>
              )}

              {!loading && jobs.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-sm text-gray-500">
                    Noch keine Jobs angelegt. Verwende das Formular oben, um den ersten Job zu erstellen.
                  </td>
                </tr>
              )}

              {!loading &&
                jobs.map((job) => {
                  const statusBadge = jobStatusBadge(job)
                  const runStatus =
                    job.last_run_status === 'error'
                      ? 'Fehler beim letzten Lauf'
                      : job.last_run_status === 'success'
                      ? 'Letzter Lauf erfolgreich'
                      : 'Noch kein Lauf'

                  return (
                    <tr key={job.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 align-top">
                        <div className="flex flex-col gap-1">
                          <span className="text-sm font-semibold text-gray-900">{job.name}</span>
                          <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                            {job.query && (
                              <span className="rounded-full bg-gray-100 px-2 py-0.5">
                                Suche: {job.query}
                              </span>
                            )}
                            {job.location && (
                              <span className="rounded-full bg-gray-100 px-2 py-0.5">
                                Ort: {job.location}
                              </span>
                            )}
                            {job.radius != null && (
                              <span className="rounded-full bg-gray-100 px-2 py-0.5">
                                Radius: {job.radius} km
                              </span>
                            )}
                            {job.min_price != null && (
                              <span className="rounded-full bg-gray-100 px-2 py-0.5">
                                Min: {job.min_price} €
                              </span>
                            )}
                            {job.max_price != null && (
                              <span className="rounded-full bg-gray-100 px-2 py-0.5">
                                Max: {job.max_price} €
                              </span>
                            )}
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4 align-top">
                        <div className="flex flex-col gap-1 text-sm text-gray-700">
                          <span>{formatInterval(job.interval_seconds)}</span>
                          <span className="text-xs text-gray-500">
                            Bis zu {job.page_count} Seite{job.page_count === 1 ? '' : 'n'} pro Lauf
                          </span>
                          {job.last_result_count != null && (
                            <span className="text-xs text-gray-500">
                              Zuletzt gespeicherte Artikel: {job.last_result_count}
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="px-6 py-4 align-top">
                        <div className="flex flex-col gap-2">
                          <span
                            className={`inline-flex w-fit items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${statusBadge.className}`}
                          >
                            {job.is_active ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
                            {statusBadge.label}
                          </span>
                          <span
                            className={`inline-flex w-fit items-center gap-2 rounded-full px-3 py-1 text-xs ${
                              job.last_run_status === 'error'
                                ? 'bg-red-100 text-red-700'
                                : job.last_run_status === 'success'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {job.last_run_status === 'error' ? <AlertTriangle className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                            {runStatus}
                          </span>
                          {job.last_run_status === 'error' && job.last_run_message && (
                            <span className="text-xs text-red-600">{job.last_run_message}</span>
                          )}
                        </div>
                      </td>

                      <td className="px-6 py-4 align-top text-sm text-gray-700">
                        <div className="space-y-1">
                          <div>
                            <span className="font-medium text-gray-600">Letzter Lauf:</span>{' '}
                            {formatTimestamp(job.last_run_at)}
                          </div>
                          <div>
                            <span className="font-medium text-gray-600">Nächster Lauf:</span>{' '}
                            {formatTimestamp(job.next_run_at)}
                          </div>
                          {job.last_run_duration_seconds != null && (
                            <div className="text-xs text-gray-500">
                              Dauer: {job.last_run_duration_seconds.toFixed(1)} Sek.
                            </div>
                          )}
                        </div>
                      </td>

                      <td className="px-6 py-4 align-top">
                        <div className="flex flex-wrap gap-2">
                          {job.is_active ? (
                            <button
                              type="button"
                              onClick={() => void handleStop(job.id)}
                              className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
                            >
                              <Pause className="h-4 w-4" />
                              Stoppen
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => void handleStart(job.id)}
                              className="inline-flex items-center gap-2 rounded-md bg-green-600 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
                            >
                              <Play className="h-4 w-4" />
                              Starten
                            </button>
                          )}

                          <button
                            type="button"
                            onClick={() => void handleRunNow(job.id)}
                            className="inline-flex items-center gap-2 rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-medium text-blue-700 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-300"
                          >
                            <Clock className="h-4 w-4" />
                            Jetzt ausführen
                          </button>

                          <button
                            type="button"
                            onClick={() => handleEdit(job)}
                            className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-2 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
                          >
                            <Settings className="h-4 w-4" />
                            Bearbeiten
                          </button>

                          <button
                            type="button"
                            onClick={() => void handleDelete(job.id)}
                            className="inline-flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs font-medium text-red-600 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-300"
                          >
                            <Trash2 className="h-4 w-4" />
                            Löschen
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
