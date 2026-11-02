import { useStaffHttp } from '../shared/http'
import type { Offer, OfferCreateProductResult, OfferFilters, OfferList, Supplier, SupplierSyncResult } from './types'

export const useOffersApi = () => {
  const http = useStaffHttp()

  return {
    listSuppliers: () => http<Supplier[]>('/manager/suppliers/'),
    syncSupplier: (id: number) => http<SupplierSyncResult>(`/manager/suppliers/${id}/sync`, { method: 'POST' }),
    listOffers: (filters: OfferFilters = {}) => http<OfferList>('/manager/offers/', { query: filters }),
    linkOffer: (id: number, productId: number) =>
      http<Offer>(`/manager/offers/${id}/link`, { method: 'POST', body: { product_id: productId } }),
    unlinkOffer: (id: number) => http<Offer>(`/manager/offers/${id}/unlink`, { method: 'POST' }),
    createProduct: (id: number, categoryId: number) =>
      http<OfferCreateProductResult>(`/manager/offers/${id}/create-product`, {
        method: 'POST',
        body: { category_id: categoryId },
      }),
  }
}
