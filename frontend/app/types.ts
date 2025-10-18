export interface SearchParams {
  query?: string
  location?: string
  radius?: number
  category?: string
  priceMin?: number
  priceMax?: number
  sortBy?: string
  sellerType?: 'private' | 'business'
  sellerBadges?: string[]
  shippingOption?: 'all' | 'shipping' | 'pickup'
}

export interface SellerInfo {
  name?: string
  since?: string
  type?: 'private' | 'business' | string
  badges: string[]
}

export interface ShippingInfo {
  raw?: string | null
  code?: 'shipping' | 'pickup' | 'both' | 'unknown'
  label: string
  description?: string
}

export interface SearchResult {
  id: string
  title: string
  price: string
  location: string
  image?: string
  url: string
  description?: string
  created_at?: string
  seller?: SellerInfo
  shipping?: ShippingInfo
}
