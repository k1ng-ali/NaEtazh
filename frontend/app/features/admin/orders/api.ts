import type { OrderStatus } from '~/features/checkout/types'
import { useAdminHttp } from '../shared/http'
import type { OrderAdmin, OrderFilters, OrderRowList } from './types'

export const useAdminOrdersApi = () => {
  const http = useAdminHttp()

  return {
    listOrders: (filters: OrderFilters = {}) => http<OrderRowList>('/admin/orders/', { query: filters }),
    getOrder: (id: number) => http<OrderAdmin>(`/admin/orders/${id}`),
    changeStatus: (id: number, status: OrderStatus) =>
      http<OrderAdmin>(`/admin/orders/${id}/status`, { method: 'POST', body: { status } }),
    setServiceCost: (id: number, serviceId: number, cost: string | null) =>
      http<OrderAdmin>(`/admin/orders/${id}/services/${serviceId}/cost`, { method: 'PUT', body: { cost } }),
  }
}
