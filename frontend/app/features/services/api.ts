import { useHttp } from '~/shared/api/http'
import type { ServiceRequestCreated, ServiceRequestPayload, ShopContacts, ShopService } from './types'

export const useServicesApi = () => {
  const http = useHttp()

  return {
    listServices: () => http<ShopService[]>('/services/'),
    getContacts: () => http<ShopContacts>('/shop/contacts'),
    getService: (slug: string) => http<ShopService>(`/services/${encodeURIComponent(slug)}`),
    createRequest: (payload: ServiceRequestPayload) =>
      http<ServiceRequestCreated>('/service-requests/', { method: 'POST', body: payload }),
  }
}

// Цена на карточке, пока владелец её не задал
export const PRICE_ON_CALL = 'Цену назовём после звонка'

// «+7 (3452) 50-50-50» → «tel:+73452505050»
export const telHref = (phone: string) => `tel:${phone.replace(/[^\d+]/g, '')}`
