export type ProductStatus = 'draft' | 'published' | 'archived'

export interface AdminCategory {
  id: number
  parent_id: number | null
  name: string
  slug: string
  position: number
  is_active: boolean
  // Своя картинка плитки на главной, пусто — фото товара раздела
  image: string | null
  product_count: number
}

export interface CategoryPayload {
  name?: string
  slug?: string | null
  parent_id?: number | null
  position?: number
  is_active?: boolean
}

export interface Warehouse {
  id: number
  name: string
  address: string | null
}

export interface Stock {
  warehouse_id: number
  warehouse_name: string
  quantity: string
  reserved: string
  unit_cost: string | null
}

export interface ProductOffer {
  id: number
  supplier_name: string
  name: string
  url: string | null
  price: string
  quantity: string
  is_active: boolean
}

export interface AdminProduct {
  id: number
  category_id: number
  sku: string
  name: string
  slug: string
  description: string | null
  unit: string
  price: string
  is_price_manual: boolean
  weight_kg: string | null
  volume_m3: string | null
  length_mm: number | null
  images: string[]
  attributes: Record<string, string>
  status: ProductStatus
  created_at: string
  updated_at: string
  stock: Stock[]
  offers: ProductOffer[]
}

export interface ProductRow {
  id: number
  category_id: number
  sku: string
  name: string
  unit: string
  price: string
  is_price_manual: boolean
  status: ProductStatus
  image: string | null
  stock_quantity: string
  offer_price: string | null
  offer_quantity: string | null
}

export interface ProductRowList {
  items: ProductRow[]
  total: number
}

export interface ProductFilters {
  search?: string
  category_id?: number
  status?: ProductStatus
  skip?: number
  limit?: number
}

export interface ProductPayload {
  category_id?: number
  name?: string
  sku?: string | null
  slug?: string | null
  description?: string | null
  unit?: string
  price?: string
  is_price_manual?: boolean
  weight_kg?: string | null
  volume_m3?: string | null
  length_mm?: number | null
  attributes?: Record<string, string>
  images?: string[]
  status?: ProductStatus
}

export interface StockPayload {
  warehouse_id: number
  quantity: string
  unit_cost: string | null
}
