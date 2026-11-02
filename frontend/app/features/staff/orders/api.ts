import type { OrderStatus } from '~/features/checkout/types'
import { useStaffHttp } from '../shared/http'
import type { Courier, DeliveryPayload, OrderAdmin, OrderFilters, OrderMoney, OrderRowList } from './types'

export const useStaffOrdersApi = () => {
  const http = useStaffHttp()

  return {
    // ── Менеджер и владелец ──
    listOrders: (filters: OrderFilters = {}) => http<OrderRowList>('/manager/orders/', { query: filters }),
    getOrder: (id: number) => http<OrderAdmin>(`/manager/orders/${id}`),
    changeStatus: (id: number, status: OrderStatus) =>
      http<OrderAdmin>(`/manager/orders/${id}/status`, { method: 'POST', body: { status } }),
    setDelivery: (id: number, payload: DeliveryPayload) =>
      http<OrderAdmin>(`/manager/orders/${id}/delivery`, { method: 'PUT', body: payload }),
    listCouriers: () => http<Courier[]>('/manager/couriers/'),

    // ── Только владелец: расходы и прибыль ──
    getOrderMoney: (id: number) => http<OrderMoney>(`/admin/orders/${id}`),
    setServiceCost: (id: number, serviceId: number, cost: string | null) =>
      http<OrderMoney>(`/admin/orders/${id}/services/${serviceId}/cost`, { method: 'PUT', body: { cost } }),
  }
}
