'use client'

import { useState } from 'react'
import { SearchResult, SellerInfo, ShippingInfo } from '../types'
import {
  MapPin,
  Euro,
  ExternalLink,
  Clock,
  Grid3x3,
  List,
  Truck,
  BadgeCheck,
  UserCircle2,
} from 'lucide-react'

interface SearchResultsProps {
  results: SearchResult[]
}

export default function SearchResults({ results }: SearchResultsProps) {
  const [viewMode, setViewMode] = useState<'gallery' | 'table'>('table')

  return (
    <div>
      {/* Results Header */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">
          {results.length} Ergebnis{results.length !== 1 ? 'se' : ''} gefunden
        </h2>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-2 bg-white rounded-lg border border-gray-200 p-1">
          <button
            onClick={() => setViewMode('gallery')}
            className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'gallery'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <Grid3x3 className="h-4 w-4" />
            Galerie
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              viewMode === 'table'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            <List className="h-4 w-4" />
            Liste
          </button>
        </div>
      </div>

      {/* Gallery View */}
      {viewMode === 'gallery' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.map((result) => (
          <div
            key={result.id}
            className="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-200 overflow-hidden border border-gray-200 group"
          >
            {/* Image */}
            {result.image && (
              <div className="relative h-48 bg-gray-200 overflow-hidden">
                <img
                  src={result.image}
                  alt={result.title}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                />
              </div>
            )}
            {!result.image && (
              <div className="h-48 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            )}

            {/* Content */}
            <div className="p-4">
              {/* Title */}
              <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-blue-600 transition-colors">
                {result.title}
              </h3>

              {/* Price */}
              <div className="flex items-center text-2xl font-bold text-blue-600 mb-3">
                <Euro className="h-6 w-6 mr-1" />
                {result.price}
              </div>

              {/* Location */}
              {result.location && (
                <div className="flex items-center text-sm text-gray-600 mb-2">
                  <MapPin className="h-4 w-4 mr-1 flex-shrink-0" />
                  <span className="truncate">{result.location}</span>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 mb-3">
                {result.created_at && (
                  <span className="inline-flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDate(result.created_at)}
                  </span>
                )}
                <ShippingBadge shipping={result.shipping} />
              </div>

              <SellerSummary seller={result.seller} className="mb-3" />

              {/* Description */}
              <DescriptionTooltip
                description={result.description}
                previewClassName="line-clamp-2"
                maxPreviewChars={120}
                containerClassName="mb-4"
              />

              {/* View Button */}
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center w-full px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Anzeige ansehen
                <ExternalLink className="ml-2 h-4 w-4" />
              </a>
            </div>
          </div>
          ))}
        </div>
      )}

      {/* Table View */}
      {viewMode === 'table' && (
        <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Bild
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Artikel
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Preis
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Beschreibung
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Aktion
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {results.map((result) => (
                  <tr key={result.id} className="hover:bg-gray-50 transition-colors">
                    {/* Image */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="h-20 w-20 rounded-lg overflow-hidden bg-gray-100 flex-shrink-0">
                        {result.image ? (
                          <img
                            src={result.image}
                            alt={result.title}
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="h-full w-full flex items-center justify-center">
                            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                          </div>
                        )}
                      </div>
                    </td>

                    {/* Article Name */}
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900 max-w-xs">
                        {result.title}
                      </div>
                      {result.location && (
                        <div className="flex items-center text-sm text-gray-500 mt-1">
                          <MapPin className="h-3 w-3 mr-1" />
                          {result.location}
                        </div>
                      )}
                      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400 mt-2">
                        {result.created_at && (
                          <span className="inline-flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {formatDate(result.created_at)}
                          </span>
                        )}
                        <ShippingBadge shipping={result.shipping} />
                      </div>
                      <SellerSummary seller={result.seller} className="mt-2" />
                    </td>

                    {/* Price */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-lg font-bold text-blue-600">
                        <Euro className="h-5 w-5 mr-1" />
                        {result.price}
                      </div>
                    </td>

                    {/* Description */}
                    <td className="px-6 py-4">
                      <DescriptionTooltip
                        description={result.description}
                        previewClassName="max-w-2xl line-clamp-4"
                        maxPreviewChars={180}
                      />
                    </td>

                    {/* Action */}
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <a
                        href={result.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors"
                      >
                        Ansehen
                        <ExternalLink className="ml-1 h-4 w-4" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Gerade eben'
    if (diffMins < 60) return `Vor ${diffMins} Minute${diffMins !== 1 ? 'n' : ''}`
    if (diffHours < 24) return `Vor ${diffHours} Stunde${diffHours !== 1 ? 'n' : ''}`
    if (diffDays < 7) return `Vor ${diffDays} Tag${diffDays !== 1 ? 'en' : ''}`
    
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch {
    return dateString
  }
}

interface DescriptionTooltipProps {
  description?: string
  previewClassName?: string
  containerClassName?: string
  maxPreviewChars?: number
}

function DescriptionTooltip({
  description,
  previewClassName = '',
  containerClassName = '',
  maxPreviewChars = 160,
}: DescriptionTooltipProps) {
  if (!description) {
    return (
      <div className={`text-sm text-gray-400 ${containerClassName}`}>
        Keine Beschreibung
      </div>
    )
  }

  const normalized = description.trim()
  const showTooltip = normalized.length > maxPreviewChars || normalized.includes('\n')

  return (
    <div className={`relative group ${containerClassName}`}>
      <div
        className={`text-sm text-gray-600 cursor-help focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${previewClassName}`}
        tabIndex={showTooltip ? 0 : -1}
        title={!showTooltip ? normalized : undefined}
        aria-label={showTooltip ? 'Vollständige Beschreibung anzeigen' : undefined}
      >
        {normalized}
      </div>

      {showTooltip && (
        <div className="invisible opacity-0 group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100 absolute z-50 left-0 top-full mt-2 w-96 text-sm">
          <div className="pointer-events-none bg-white border border-gray-200 rounded-lg shadow-xl p-4">
            <div className="font-semibold text-gray-900 mb-2">Vollständige Beschreibung</div>
            <div className="max-h-64 overflow-y-auto text-gray-700 whitespace-pre-wrap pointer-events-auto">
              {normalized}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

interface SellerSummaryProps {
  seller?: SellerInfo
  className?: string
}

function SellerSummary({ seller, className = '' }: SellerSummaryProps) {
  if (!seller) return null

  const hasName = Boolean(seller.name)
  const hasBadges = Array.isArray(seller.badges) && seller.badges.length > 0

  if (!hasName && !hasBadges) {
    return null
  }

  const sellerTypeLabel =
    seller.type === 'business'
      ? 'Gewerblicher Anbieter'
      : seller.type === 'private'
        ? 'Privater Anbieter'
        : undefined

  return (
    <div className={`space-y-2 ${className}`}>
      {hasName && (
        <div className="flex items-center text-xs font-medium text-gray-600 gap-2">
          <UserCircle2 className="h-4 w-4 text-blue-500" />
          <span>{seller.name}</span>
          {sellerTypeLabel && (
            <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700">
              {sellerTypeLabel}
            </span>
          )}
        </div>
      )}

      {seller.since && (
        <div className="text-[11px] text-gray-400 pl-6">
          Aktiv seit {seller.since}
        </div>
      )}

      {hasBadges && (
        <div className="flex flex-wrap gap-2">
          {seller.badges.slice(0, 4).map((badge) => (
            <span
              key={badge}
              className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-1 text-[11px] font-semibold text-green-700"
            >
              <BadgeCheck className="h-3 w-3" />
              {badge}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

interface ShippingBadgeProps {
  shipping?: ShippingInfo
}

function ShippingBadge({ shipping }: ShippingBadgeProps) {
  if (!shipping || shipping.code === 'unknown') {
    return null
  }

  const tone =
    shipping.code === 'shipping'
      ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
      : shipping.code === 'pickup'
        ? 'bg-amber-50 text-amber-700 border-amber-200'
        : 'bg-blue-50 text-blue-700 border-blue-200'

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${tone}`}
      title={shipping.description || shipping.raw || undefined}
    >
      <Truck className="h-3 w-3" />
      {shipping.label}
    </span>
  )
}
