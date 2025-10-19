'use client'

import { useState } from 'react'
import SearchForm from './components/SearchForm'
import SearchResults from './components/SearchResults'
import StoredListingsView from './components/StoredListingsView'
import SchedulerJobsView from './components/SchedulerJobsView'
import { SearchParams, SearchResult, SellerInfo, ShippingInfo } from './types'

export default function Home() {
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'search' | 'stored' | 'scheduler'>('search')

  const handleSearch = async (params: SearchParams) => {
    setLoading(true)
    setError(null)

    try {
      // Build query string - Map frontend params to backend API params
      const queryParams = new URLSearchParams()
      
      if (params.query) queryParams.append('query', params.query)
      if (params.location) queryParams.append('location', params.location)
      if (params.radius) queryParams.append('radius', params.radius.toString())
      if (params.priceMin) queryParams.append('min_price', params.priceMin.toString())
      if (params.priceMax) queryParams.append('max_price', params.priceMax.toString())
      if (params.category) queryParams.append('category', params.category)
      if (params.sortBy) queryParams.append('sort', params.sortBy)
      if (params.sellerType) queryParams.append('seller_type', params.sellerType)
      if (params.shippingOption && params.shippingOption !== 'all') {
        queryParams.append('shipping', params.shippingOption)
      }
      if (params.sellerBadges && params.sellerBadges.length > 0) {
        params.sellerBadges.forEach((badge) =>
          queryParams.append('seller_badge', badge)
        )
      }

      console.log('Fetching:', `/api/backend/inserate?${queryParams.toString()}`)
      // Use detailed endpoint to enrich results with seller badges and shipping options
      const response = await fetch(`/api/backend/inserate-detailed?${queryParams.toString()}`)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('API Error:', response.status, errorText)
        throw new Error(`Suche fehlgeschlagen (${response.status})`)
      }

      const data = await response.json()
      console.log('API Response:', data)
      
      // Combined endpoint returns detailed data under "data"
      const resultsArray = data.data || data.results || []
      console.log('Results array:', resultsArray, 'length:', resultsArray.length)
      
      // Map backend data structure to frontend format
      if (!Array.isArray(resultsArray)) {
        console.warn('No results array in response:', data)
        setResults([])
        return
      }

      const mappedResults = resultsArray.map((item: any) => {
        const details = item.details || {}
        const sellerBadges = Array.isArray(details.seller?.badges)
          ? details.seller.badges.filter((badge: unknown): badge is string => typeof badge === 'string' && badge.trim().length > 0)
          : []
        const sellerName = typeof details.seller?.name === 'string' ? details.seller.name.trim() : undefined
        const sellerSince = typeof details.seller?.since === 'string' ? details.seller.since.trim() : undefined
        const sellerType = details.seller?.type
        const hasSellerInfo =
          Boolean(sellerName) || Boolean(sellerSince) || sellerBadges.length > 0 || Boolean(sellerType)
        const seller: SellerInfo | undefined = hasSellerInfo
          ? {
              name: sellerName,
              since: sellerSince,
              type: sellerType,
              badges: sellerBadges,
            }
          : undefined

        const locationData = details.location || {}
        const primaryLocation = [locationData.zip, locationData.city]
          .filter(Boolean)
          .join(' ')
          .trim()
        const locationParts = [
          primaryLocation || null,
          locationData.state || null,
        ].filter(Boolean)
        const locationFormatted = locationParts.length > 0 ? locationParts.join(', ') : ''

        const shippingDetail =
          details.details?.Versand ??
          details.details?.['Versandart'] ??
          details.details?.['Lieferung'] ??
          null

        const shipping: ShippingInfo = deriveShippingInfo(
          details.delivery,
          shippingDetail
        )

        const createdAt =
          details.extra_info?.created_at ||
          item.created_at ||
          null

        return {
          id: item.adid || `${Date.now()}-${Math.random()}`,
          title: item.title || 'Kein Titel',
          price: item.price || 'Preis auf Anfrage',
          location: locationFormatted || item.location || '',
          image: item.image,
          url: item.url || '#',
          description: item.description || '',
          created_at: createdAt || undefined,
          seller,
          shipping,
        }
      })
      
      console.log('Mapped results:', mappedResults.length, 'items')
      setResults(mappedResults)
    } catch (err) {
      console.error('Search error:', err)
      const errorMessage = err instanceof Error ? err.message : 'Ein Fehler ist aufgetreten'
      setError(errorMessage)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Kleinanzeigen-Agent</h1>
                <p className="text-sm text-gray-500">Intelligente Kleinanzeigen Suche</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex flex-wrap items-center gap-4">
          <div className="inline-flex rounded-lg border border-gray-200 bg-white p-1">
            <button
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'search'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('search')}
              type="button"
            >
              Live Suche
            </button>
            <button
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'stored'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('stored')}
              type="button"
            >
              Gespeicherte Artikel
            </button>
            <button
              className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'scheduler'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('scheduler')}
              type="button"
            >
              Scheduler
            </button>
          </div>
        </div>

        {activeTab === 'search' ? (
          <>
            <div className="mb-8">
              <SearchForm onSearch={handleSearch} loading={loading} />
            </div>

            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                <div className="flex items-center">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                  {error}
                </div>
              </div>
            )}

            {loading && (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            )}

            {!loading && results.length > 0 && <SearchResults results={results} />}

            {!loading && !error && results.length === 0 && (
              <div className="text-center py-12">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <h3 className="mt-2 text-lg font-medium text-gray-900">Keine Ergebnisse</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Starte eine Suche, um Kleinanzeigen zu finden.
                </p>
              </div>
            )}
          </>
        ) : activeTab === 'stored' ? (
          <StoredListingsView />
        ) : (
          <SchedulerJobsView />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2025 Kleinanzeigen-Agent. Powered by FastAPI + Next.js
          </p>
        </div>
      </footer>
    </div>
  )
}

function deriveShippingInfo(
  deliveryCode?: string | null,
  rawText?: string | null
): ShippingInfo {
  const normalizedRaw = rawText?.toLowerCase() ?? ''
  const normalizedDelivery = deliveryCode?.toLowerCase() ?? ''
  let code: ShippingInfo['code'] = 'unknown'
  let label = 'Keine Versandangabe'
  let description: string | undefined

  if (normalizedRaw) {
    description = rawText ?? undefined
  }

  const combined = `${normalizedDelivery} ${normalizedRaw}`.trim()

  if (combined.includes('versand') && combined.includes('abholung')) {
    code = 'both'
    label = 'Versand & Abholung'
  } else if (
    combined.includes('nur versand') ||
    combined.includes('nur-versand') ||
    combined.includes('only shipping')
  ) {
    code = 'shipping'
    label = 'Nur Versand'
  } else if (
    combined.includes('nur abholung') ||
    combined.includes('selbstabholung') ||
    combined.includes('pickup')
  ) {
    code = 'pickup'
    label = 'Nur Abholung'
  } else if (combined.includes('versand') || normalizedDelivery === 'shipping') {
    code = 'shipping'
    label = 'Versand möglich'
  } else if (normalizedDelivery === 'pickup') {
    code = 'pickup'
    label = 'Abholung vor Ort'
  }

  return {
    raw: rawText ?? deliveryCode ?? null,
    code,
    label,
    description,
  }
}
