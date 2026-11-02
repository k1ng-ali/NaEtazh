export type LiftingType = 'none' | 'lift' | 'stairs'
export type Availability = 'in_stock' | 'on_order' | 'unavailable'

// Снимок товара в корзине, чтобы показать её сразу, до ответа сервера
export interface CartItem {
  product_id: number
  slug: string
  name: string
  unit: string
  price: string
  image: string | null
  quantity: number
}

export interface QuotePayload {
  items: { product_id: number; quantity: number }[]
  building_code?: string | null
  floor?: number | null
  lifting_type: LiftingType
}

export interface QuoteLine {
  product_id: number
  slug: string
  name: string
  unit: string
  image: string | null
  quantity: string
  unit_price: string
  total: string
  availability: Availability
  available_quantity: string
  too_long_for_lift: boolean
}

export interface Service {
  type: 'delivery' | 'lifting'
  name: string
  price: string
}

export interface Quote {
  lines: QuoteLine[]
  removed_product_ids: number[]
  services: Service[]
  goods_total: string
  services_total: string
  total: string
  total_weight_kg: string
  weight_unknown: boolean
  services_unknown: boolean
  can_order: boolean
}
