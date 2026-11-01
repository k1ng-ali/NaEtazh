export interface Category {
  id: number
  parent_id: number | null
  name: string
  slug: string
  position: number
}

export interface Product {
  id: number
  category_id: number
  sku: string
  name: string
  slug: string
  description: string | null
  unit: string
  price: string
  weight_kg: string | null
  length_mm: number | null
  images: string[]
  attributes: Record<string, unknown>
}

export interface ProductList {
  items: Product[]
  total: number
}

export interface ProductFilters {
  category?: string
  search?: string
  skip?: number
  limit?: number
}
