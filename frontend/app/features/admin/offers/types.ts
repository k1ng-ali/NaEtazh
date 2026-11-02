export type OfferMatch = 'unmatched' | 'matched' | 'all'

export interface SyncSummary {
  total: number
  created: number
  updated: number
  hidden: number
  prices_updated: number
}

export interface Supplier {
  id: number
  code: string
  name: string
  feed_url: string | null
  is_active: boolean
  last_synced_at: string | null
  last_sync_error: string | null
  last_sync_summary: SyncSummary | null
  offers_active: number
  offers_unmatched: number
}

export interface SupplierSyncResult {
  ok: boolean
  error: string | null
  supplier: Supplier
}

export interface Offer {
  id: number
  supplier_id: number
  product_id: number | null
  product_name: string | null
  external_id: string
  name: string
  url: string | null
  vendor: string | null
  category_name: string | null
  picture_url: string | null
  weight_kg: string | null
  price: string
  quantity: string
  is_active: boolean
  last_seen_at: string
}

export interface OfferList {
  items: Offer[]
  total: number
}

export interface OfferFilters {
  supplier_id?: number
  match?: OfferMatch
  search?: string
  in_stock?: boolean
  skip?: number
  limit?: number
}

export interface OfferCreateProductResult {
  product_id: number
  offer: Offer
}
