import type { LiftingType } from '~/features/cart/types'
import type { ContactChannel, DeliverySlot, OrderStatus } from '~/features/checkout/types'

export interface CourierOrderRow {
  id: number
  status: OrderStatus
  planned_date: string | null
  planned_slot: DeliverySlot | null
  address: string
  lifting_type: LiftingType
  total: string
}

export interface CourierOrder {
  id: number
  status: OrderStatus
  planned_date: string | null
  planned_slot: DeliverySlot | null
  address: string
  map_address: string
  entrance: string | null
  floor: string | null
  apartment: string | null
  lifting_type: LiftingType
  customer_name: string
  customer_phone: string
  contact_channel: ContactChannel | null
  comment: string | null
  lines: { name: string; unit: string; quantity: string }[]
  total: string
  cash_received: string | null
  delivered_at: string | null
}
