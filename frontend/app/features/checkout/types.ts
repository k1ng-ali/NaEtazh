import type { LiftingType, QuotePayload, Service } from '~/features/cart/types'

export type OrderStatus = 'new' | 'checking' | 'confirmed' | 'in_delivery' | 'delivered' | 'canceled'
export type DeliverySlot = 'morning' | 'day' | 'evening'
export type ContactChannel = 'call' | 'whatsapp' | 'telegram'
export type MissingItemPolicy = 'call' | 'replace' | 'skip'

export interface OrderPayload extends QuotePayload {
  customer_name: string
  customer_phone: string
  contact_channel: ContactChannel
  missing_item_policy: MissingItemPolicy
  address_text: string | null
  entrance: string | null
  apartment: string | null
  delivery_date: string | null
  delivery_slot: DeliverySlot | null
  comment: string | null
  source_code: string | null
  consent: true
}

export interface OrderCreated {
  number: number
  public_token: string
}

export interface OrderPublic {
  number: number
  status: OrderStatus
  created_at: string
  address: string
  lifting_type: LiftingType
  delivery_date: string | null
  delivery_slot: DeliverySlot | null
  lines: { name: string; unit: string; quantity: string; unit_price: string; total: string }[]
  services: Service[]
  goods_total: string
  services_total: string
  total: string
}
