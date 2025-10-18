'use client'

import { useState } from 'react'
import SearchForm from './components/SearchForm'
import SearchResults from './components/SearchResults'
import { SearchParams, SearchResult } from './types'

export default function Home() {
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

      console.log('Fetching:', `/api/backend/inserate?${queryParams.toString()}`)
      const response = await fetch(`/api/backend/inserate?${queryParams.toString()}`)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('API Error:', response.status, errorText)
        throw new Error(`Suche fehlgeschlagen (${response.status})`)
      }

      const data = await response.json()
      console.log('API Response:', data)
      
      // API returns "results" not "data"
      const resultsArray = data.results || data.data || []
      console.log('Results array:', resultsArray, 'length:', resultsArray.length)
      
      // Map backend data structure to frontend format
      if (!Array.isArray(resultsArray)) {
        console.warn('No results array in response:', data)
        setResults([])
        return
      }

      const mappedResults = resultsArray.map((item: any) => ({
        id: item.adid || `${Date.now()}-${Math.random()}`,
        title: item.title || 'Kein Titel',
        price: item.price || 'Preis auf Anfrage',
        location: item.location || '',
        image: item.image,
        url: item.url || '#',
        description: item.description || '',
        created_at: item.created_at
      }))
      
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
        {/* Search Form */}
        <div className="mb-8">
          <SearchForm onSearch={handleSearch} loading={loading} />
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Results */}
        {!loading && results.length > 0 && (
          <SearchResults results={results} />
        )}

        {/* Empty State */}
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
