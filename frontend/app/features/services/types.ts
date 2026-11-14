export interface ShopService {
  slug: string
  name: string
  summary: string | null
  description: string | null
  // «от 1 500 ₽», пусто — цену называет менеджер
  price_text: string | null
  // Телефон услуги или общий телефон магазина, пусто — кнопку «Позвонить» не показываем
  phone: string | null
}

export interface ShopContacts {
  phone: string | null
}

export interface ServiceRequestPayload {
  service_slug: string
  customer_name: string
  customer_phone: string
  building_code: string | null
  address_text: string | null
  apartment: string | null
  preferred_date: string | null
  comment: string | null
  source_code: string | null
  consent: true
}

export interface ServiceRequestCreated {
  number: number
}
