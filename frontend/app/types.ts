export interface SearchParams {
  query?: string
  location?: string
  radius?: number
  category?: string
  priceMin?: number
  priceMax?: number
  sortBy?: string
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
}
