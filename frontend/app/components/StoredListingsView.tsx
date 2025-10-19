'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  ArrowUpDown,
  Clock,
  Database,
  ExternalLink,
  Filter,
  MapPin,
  RefreshCcw,
  Tag,
} from 'lucide-react'

import type { StoredListing } from '../types'

interface Filters {
  queryName: string
  status: string
  search: string
  limit: number
}

const statusOptions: Array<{ value: string; label: string }> = [
  { value: '', label: 'Alle Stati' },
  { value: 'active', label: 'Aktiv' },
  { value: 'reserved', label: 'Reserviert' },
  { value: 'sold', label: 'Verkauft' },
  { value: 'deleted', label: 'Gelöscht' },
]

const defaultFilters: Filters = {
  queryName: '',
  status: '',
  search: '',
  limit: 25,
}

export default function StoredListingsView() {
  const [filters, setFilters] = useState<Filters>(defaultFilters)
  const [appliedFilters, setAppliedFilters] = useState<Filters>(defaultFilters)
  const [listings, setListings] = useState<StoredListing[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState<number | null>(null)

  const fetchListings = useCallback(async () => {
    setLoading(true)
    setError(null)
    setTotalCount(null)

    try {
      const params = new URLSearchParams()
      params.set('limit', appliedFilters.limit.toString())
      if (appliedFilters.queryName.trim()) {
        params.set('query_name', appliedFilters.queryName.trim())
      }
      if (appliedFilters.status) {
        params.set('status', appliedFilters.status)
      }
      if (appliedFilters.search.trim()) {
        params.set('search', appliedFilters.search.trim())
      }

      const response = await fetch(`/api/backend/stored-listings?${params.toString()}`)
      if (!response.ok) {
        throw new Error(`Fehler beim Laden (${response.status})`)
      }

      const data = await response.json()
      const normalized: StoredListing[] = Array.isArray(data.items)
        ? data.items.map((item: StoredListing) => ({
            ...item,
            image_urls: Array.isArray(item.image_urls) ? item.image_urls : [],
            seller: item.seller
              ? {
                  ...item.seller,
                  badges: Array.isArray(item.seller.badges) ? item.seller.badges : [],
                }
              : undefined,
          }))
        : []

      setListings(normalized)
      setTotalCount(
        typeof data.total === 'number'
          ? data.total
          : normalized.length
      )
      setLastUpdated(new Date().toISOString())
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unbekannter Fehler'
      setError(message)
      setListings([])
      setTotalCount(null)
    } finally {
      setLoading(false)
    }
  }, [appliedFilters])

  useEffect(() => {
    void fetchListings()
  }, [fetchListings])

  const priceFormatter = useMemo(
    () =>
      new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }),
    []
  )

  return (
    <div className="space-y-6">
      <section className="bg-white border border-gray-200 rounded-xl shadow-sm">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-indigo-600">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Gespeicherte Artikel</h2>
              <p className="text-sm text-gray-500">
                Ergebnisse aus den automatischen Suchläufen
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {typeof totalCount === 'number' && (
              <span className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-indigo-700">
                <Database className="h-4 w-4" />
                {totalCount} Artikel gespeichert
              </span>
            )}
            <button
              type="button"
              onClick={() => setAppliedFilters({ ...filters })}
              className="inline-flex items-center gap-2 rounded-md border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              disabled={loading}
            >
              <RefreshCcw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Aktualisieren
            </button>
          </div>
        </header>

        <div className="px-6 py-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
              <span>Job-Name</span>
              <input
                type="text"
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="z. B. woom-3"
                value={filters.queryName}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, queryName: event.target.value }))
                }
              />
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
              <span>Status</span>
              <div className="relative">
                <Filter className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <select
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 pl-9 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={filters.status}
                  onChange={(event) =>
                    setFilters((prev) => ({ ...prev, status: event.target.value }))
                  }
                >
                  {statusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
              <span>Suche im Titel/Beschreibung</span>
              <input
                type="text"
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="z. B. leicht gebraucht"
                value={filters.search}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, search: event.target.value }))
                }
              />
            </label>

            <label className="flex flex-col gap-2 text-sm font-medium text-gray-700">
              <span>Limit</span>
              <select
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={filters.limit}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, limit: Number(event.target.value) || 25 }))
                }
              >
                {[10, 25, 50, 100].map((value) => (
                  <option key={value} value={value}>
                    {value} Einträge
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <ArrowUpDown className="h-4 w-4" />
              <span>Sortierung: Neueste zuerst</span>
            </div>
            {lastUpdated && (
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4" />
                <span>Zuletzt aktualisiert: {formatRelative(lastUpdated)}</span>
              </div>
            )}
          </div>
        </div>
      </section>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <section className="bg-white border border-gray-200 rounded-xl shadow-sm">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Artikel
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Preis
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Beobachtung
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Aktion
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {loading && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-500">
                    Lädt gespeicherte Artikel...
                  </td>
                </tr>
              )}

              {!loading && listings.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-sm text-gray-500">
                    Keine gespeicherten Artikel gefunden. Passe die Filter an oder warte auf den nächsten Lauf.
                  </td>
                </tr>
              )}

              {!loading &&
                listings.map((listing) => {
                  const priceLabel = formatPrice(priceFormatter, listing)
                  const firstSeen = formatRelative(listing.first_seen_at)
                  const lastSeen = formatRelative(listing.last_seen_at)
                  const primaryImage = listing.thumbnail_url || listing.image_urls[0]

                  return (
                    <tr key={listing.external_id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-start gap-4">
                          <div className="h-20 w-28 flex-shrink-0 overflow-hidden rounded-lg bg-gray-100">
                            {primaryImage ? (
                              <img
                                src={primaryImage}
                                alt={listing.title ?? 'Artikelbild'}
                                className="h-full w-full object-cover"
                              />
                            ) : (
                              <div className="flex h-full w-full items-center justify-center text-gray-400">
                                <Tag className="h-6 w-6" />
                              </div>
                            )}
                          </div>
                          <div className="space-y-2">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-semibold text-gray-900">
                                {listing.title ?? 'Unbekannter Titel'}
                              </span>
                              {listing.query_name && (
                                <span className="inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700">
                                  <Database className="h-3 w-3" />
                                  {listing.query_name}
                                </span>
                              )}
                            </div>
                            {listing.location && (
                              <div className="flex items-center gap-1 text-xs text-gray-500">
                                <MapPin className="h-3 w-3" />
                                {[listing.location.zip, listing.location.city, listing.location.state]
                                  .filter(Boolean)
                                  .join(' ')}
                              </div>
                            )}
                            {listing.description && (
                              <p className="max-w-xl text-xs text-gray-500 line-clamp-2">
                                {listing.description}
                              </p>
                            )}
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4 align-top text-sm text-gray-900">{priceLabel}</td>

                      <td className="px-6 py-4 align-top">
                        <StatusBadge status={listing.status} />
                      </td>

                      <td className="px-6 py-4 align-top text-xs text-gray-500">
                        <div className="space-y-1">
                          <div>
                            <span className="font-medium text-gray-700">Erst gesehen:</span> {firstSeen}
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">Zuletzt gesehen:</span> {lastSeen}
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4 align-top text-right">
                        <div className="flex flex-col items-end gap-2">
                          <a
                            href={listing.url ?? '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                          >
                            Anzeigenseite
                            <ExternalLink className="h-4 w-4" />
                          </a>
                          <div className="text-[11px] text-gray-400">
                            ID: {listing.external_id}
                          </div>
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

function formatPrice(formatter: Intl.NumberFormat, listing: StoredListing): string {
  if (listing.price_amount) {
    const numeric = Number(listing.price_amount)
    if (!Number.isNaN(numeric)) {
      const label = formatter.format(numeric)
      return listing.price_negotiable ? `${label} (VB)` : label
    }
    return `${listing.price_amount} ${listing.price_currency ?? ''}`.trim()
  }
  if (listing.price_text) {
    return listing.price_text
  }
  return 'Preis unbekannt'
}

function formatRelative(dateString: string): string {
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()

    const minutes = Math.round(diffMs / 60000)
    if (minutes < 1) return 'Gerade eben'
    if (minutes < 60) return `Vor ${minutes} Minute${minutes === 1 ? '' : 'n'}`

    const hours = Math.round(minutes / 60)
    if (hours < 24) return `Vor ${hours} Stunde${hours === 1 ? '' : 'n'}`

    const days = Math.round(hours / 24)
    if (days < 7) return `Vor ${days} Tag${days === 1 ? '' : 'en'}`

    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return dateString
  }
}

interface StatusBadgeProps {
  status?: string | null
}

function StatusBadge({ status }: StatusBadgeProps) {
  if (!status) {
    return (
      <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-1 text-[11px] font-medium text-gray-600">
        Unbekannt
      </span>
    )
  }

  const tone =
    status === 'active'
      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
      : status === 'reserved'
        ? 'bg-amber-50 text-amber-700 border border-amber-200'
        : status === 'sold'
          ? 'bg-red-50 text-red-700 border border-red-200'
          : 'bg-gray-100 text-gray-700 border border-gray-200'

  const label =
    status === 'active'
      ? 'Aktiv'
      : status === 'reserved'
        ? 'Reserviert'
        : status === 'sold'
          ? 'Verkauft'
          : status === 'deleted'
            ? 'Gelöscht'
            : status

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-semibold capitalize ${tone}`}>
      {label}
    </span>
  )
}
