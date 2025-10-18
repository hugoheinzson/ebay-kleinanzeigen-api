'use client'

import { useState } from 'react'
import { SearchParams } from '../types'
import { Search, MapPin, Euro, SlidersHorizontal } from 'lucide-react'

interface SearchFormProps {
  onSearch: (params: SearchParams) => void
  loading: boolean
}

export default function SearchForm({ onSearch, loading }: SearchFormProps) {
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')
  const [radius, setRadius] = useState<number>(50)
  const [category, setCategory] = useState('')
  const [priceMin, setPriceMin] = useState<number | undefined>()
  const [priceMax, setPriceMax] = useState<number | undefined>()
  const [sortBy, setSortBy] = useState('RELEVANCE')
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const params: SearchParams = {
      query,
      location: location || undefined,
      radius: radius || undefined,
      category: category || undefined,
      priceMin,
      priceMax,
      sortBy,
    }

    onSearch(params)
  }

  const categories = [
    { value: '', label: 'Alle Kategorien' },
    { value: '27', label: 'Auto, Rad & Boot' },
    { value: '210', label: 'Elektronik' },
    { value: '23', label: 'Familie, Kind & Baby' },
    { value: '17', label: 'Freizeit, Hobby & Nachbarschaft' },
    { value: '14', label: 'Haus & Garten' },
    { value: '19', label: 'Haustiere' },
    { value: '192', label: 'Immobilien' },
    { value: '279', label: 'Jobs' },
    { value: '111', label: 'Mode & Beauty' },
    { value: '5', label: 'Musik, Filme & Bücher' },
    { value: '234', label: 'Unterricht & Kurse' },
  ]

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Main Search Bar */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Was suchst du? z.B. iPhone 14, Fahrrad, Sofa..."
            className="block w-full pl-10 pr-3 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Quick Filters Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Location */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <MapPin className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Standort eingeben..."
              className="block w-full pl-10 pr-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Radius */}
          <div>
            <select
              value={radius}
              onChange={(e) => setRadius(Number(e.target.value))}
              className="block w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="10">10 km Umkreis</option>
              <option value="20">20 km Umkreis</option>
              <option value="30">30 km Umkreis</option>
              <option value="50">50 km Umkreis</option>
              <option value="100">100 km Umkreis</option>
              <option value="150">150 km Umkreis</option>
              <option value="200">200 km Umkreis</option>
            </select>
          </div>

          {/* Category */}
          <div>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="block w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {categories.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Advanced Filters Toggle */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            <SlidersHorizontal className="h-4 w-4 mr-1" />
            {showAdvanced ? 'Erweiterte Filter ausblenden' : 'Erweiterte Filter anzeigen'}
          </button>
        </div>

        {/* Advanced Filters */}
        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200">
            {/* Price Range */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Euro className="h-4 w-4 inline mr-1" />
                Preisspanne
              </label>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <input
                    type="number"
                    value={priceMin || ''}
                    onChange={(e) => setPriceMin(e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="Min. Preis"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <input
                    type="number"
                    value={priceMax || ''}
                    onChange={(e) => setPriceMax(e.target.value ? Number(e.target.value) : undefined)}
                    placeholder="Max. Preis"
                    className="block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sortierung
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="block w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="RELEVANCE">Relevanz</option>
                <option value="PRICE_ASC">Preis aufsteigend</option>
                <option value="PRICE_DESC">Preis absteigend</option>
                <option value="DATE_DESC">Neueste zuerst</option>
                <option value="DATE_ASC">Älteste zuerst</option>
              </select>
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-lg shadow-sm text-white bg-gradient-to-r from-blue-600 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Suche läuft...
              </>
            ) : (
              <>
                <Search className="h-5 w-5 mr-2" />
                Suchen
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
