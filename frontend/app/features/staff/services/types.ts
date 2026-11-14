export type ServiceRequestStatus = 'new' | 'in_progress' | 'done' | 'canceled'

export interface ServiceRequest {
  id: number
  service_name: string
  status: ServiceRequestStatus
  customer_name: string
  customer_phone: string
  address: string
  preferred_date: string | null
  comment: string | null
  created_at: string
}

export interface ServiceRequestList {
  items: ServiceRequest[]
  total: number
}

export interface ShopServiceAdmin {
  id: number
  slug: string
  name: string
  summary: string | null
  description: string | null
  price_text: string | null
  // Свой телефон услуги, пусто — общий телефон магазина
  phone: string | null
  position: number
  is_active: boolean
}

export interface ShopContacts {
  phone: string | null
}

export interface ShopServicePayload {
  name: string
  summary: string | null
  description: string | null
  price_text: string | null
  phone: string | null
  position: number
  is_active: boolean
}
