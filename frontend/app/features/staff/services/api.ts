import { useStaffHttp } from '../shared/http'
import type {
  ServiceRequest,
  ServiceRequestList,
  ServiceRequestStatus,
  ShopContacts,
  ShopServiceAdmin,
  ShopServicePayload,
} from './types'

export const REQUEST_STATUS: Record<ServiceRequestStatus, string> = {
  new: 'Новая',
  in_progress: 'В работе',
  done: 'Выполнена',
  canceled: 'Отменена',
}

export const useStaffServicesApi = () => {
  const http = useStaffHttp()

  return {
    listRequests: (query: { status?: ServiceRequestStatus; skip?: number; limit?: number }) =>
      http<ServiceRequestList>('/manager/service-requests/', { query }),
    setRequestStatus: (id: number, status: ServiceRequestStatus) =>
      http<ServiceRequest>(`/manager/service-requests/${id}`, { method: 'PATCH', body: { status } }),
    listServices: () => http<ShopServiceAdmin[]>('/admin/services/'),
    getContacts: () => http<ShopContacts>('/admin/services/contacts'),
    setContacts: (payload: ShopContacts) =>
      http<ShopContacts>('/admin/services/contacts', { method: 'PUT', body: payload }),
    createService: (payload: ShopServicePayload) =>
      http<ShopServiceAdmin>('/admin/services/', { method: 'POST', body: payload }),
    updateService: (id: number, payload: ShopServicePayload) =>
      http<ShopServiceAdmin>(`/admin/services/${id}`, { method: 'PUT', body: payload }),
  }
}
