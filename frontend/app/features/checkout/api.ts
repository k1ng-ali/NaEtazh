import { useHttp } from '~/shared/api/http'
import type { OrderCreated, OrderPayload, OrderPublic } from './types'

export const useCheckoutApi = () => {
  const http = useHttp()

  return {
    createOrder: (payload: OrderPayload) => http<OrderCreated>('/orders/', { method: 'POST', body: payload }),
    getOrder: (token: string) => http<OrderPublic>(`/orders/${encodeURIComponent(token)}`),
  }
}
