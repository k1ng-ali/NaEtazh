import type { LiftingType } from '~/features/cart/types'
import type { ContactChannel, DeliverySlot, MissingItemPolicy, OrderStatus } from '~/features/checkout/types'

export interface OrderRow {
  id: number
  status: OrderStatus
  created_at: string
  customer_name: string
  customer_phone: string
  address: string
  delivery_date: string | null
  delivery_slot: DeliverySlot | null
  total: string
  has_supplier_items: boolean
}

export interface OrderRowList {
  items: OrderRow[]
  total: number
}

export interface OrderFilters {
  status?: OrderStatus
  search?: string
  skip?: number
  limit?: number
}

export interface Allocation {
  source_type: 'warehouse' | 'supplier'
  source_name: string
  source_url: string | null
  quantity: string
  unit_cost: string | null
}

export interface OrderLineAdmin {
  id: number
  product_id: number
  name: string
  unit: string
  quantity: string
  unit_price: string
  total: string
  allocations: Allocation[]
}

export interface ServiceLineAdmin {
  id: number
  type: 'delivery' | 'lifting'
  name: string
  price: string
  cost: string | null
}

export interface OrderAdmin {
  id: number
  public_token: string
  status: OrderStatus
  next_statuses: OrderStatus[]
  created_at: string
  updated_at: string
  customer_name: string
  customer_phone: string
  contact_channel: ContactChannel | null
  missing_item_policy: MissingItemPolicy | null
  address: string
  entrance: string | null
  floor: string | null
  apartment: string | null
  lifting_type: LiftingType
  delivery_date: string | null
  delivery_slot: DeliverySlot | null
  comment: string | null
  source_code: string | null
  lines: OrderLineAdmin[]
  services: ServiceLineAdmin[]
  goods_total: string
  services_total: string
  total: string
  goods_cost: string
  services_cost: string
  profit: string
  profit_complete: boolean
}
