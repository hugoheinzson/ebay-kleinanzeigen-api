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

export interface StoredListing {
  external_id: string
  query_name?: string | null
  title?: string | null
  description?: string | null
  price_amount?: string | null
  price_currency?: string | null
  price_negotiable?: boolean | null
  price_text?: string | null
  url?: string | null
  status?: string | null
  delivery?: string | null
  thumbnail_url?: string | null
  categories?: string[] | null
  location?: {
    zip?: string | null
    city?: string | null
    state?: string | null
  } | null
  seller?: SellerInfo | null
  details?: Record<string, unknown> | null
  features?: string[] | null
  extra_info?: Record<string, unknown> | null
  image_urls: string[]
  search_params?: Record<string, unknown> | null
  first_seen_at: string
  last_seen_at: string
  created_at: string
  updated_at: string
}

export interface SchedulerJob {
  id: number
  name: string
  query?: string | null
  location?: string | null
  radius?: number | null
  min_price?: number | null
  max_price?: number | null
  page_count: number
  interval_seconds: number
  is_active: boolean
  last_run_at?: string | null
  next_run_at?: string | null
  last_run_status?: string | null
  last_run_message?: string | null
  last_run_duration_seconds?: number | null
  last_result_count?: number | null
  created_at: string
  updated_at: string
}
