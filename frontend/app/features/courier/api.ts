import { useStaffHttp } from '~/features/staff/shared/http'
import type { CourierOrder, CourierOrderRow } from './types'

export const useCourierApi = () => {
  const http = useStaffHttp()

  return {
    listOrders: () => http<CourierOrderRow[]>('/courier/orders/'),
    getOrder: (id: number) => http<CourierOrder>(`/courier/orders/${id}`),
    start: (id: number) => http<CourierOrder>(`/courier/orders/${id}/start`, { method: 'POST' }),
    deliver: (id: number, cashReceived: string) =>
      http<CourierOrder>(`/courier/orders/${id}/deliver`, { method: 'POST', body: { cash_received: cashReceived } }),
    reportProblem: (id: number, comment: string) =>
      http<CourierOrder>(`/courier/orders/${id}/problem`, { method: 'POST', body: { comment } }),
  }
}
