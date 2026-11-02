import { useHttp } from '~/shared/api/http'
import type { Quote, QuotePayload } from './types'

export const useCartApi = () => {
  const http = useHttp()

  return {
    quote: (payload: QuotePayload) => http<Quote>('/cart/quote', { method: 'POST', body: payload }),
  }
}
