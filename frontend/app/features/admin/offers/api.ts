import { useAdminHttp } from '../shared/http'
import type { Offer, OfferCreateProductResult, OfferFilters, OfferList, Supplier, SupplierSyncResult } from './types'

export const useOffersApi = () => {
  const http = useAdminHttp()

  return {
    listSuppliers: () => http<Supplier[]>('/admin/suppliers/'),
    syncSupplier: (id: number) => http<SupplierSyncResult>(`/admin/suppliers/${id}/sync`, { method: 'POST' }),
    listOffers: (filters: OfferFilters = {}) => http<OfferList>('/admin/offers/', { query: filters }),
    linkOffer: (id: number, productId: number) =>
      http<Offer>(`/admin/offers/${id}/link`, { method: 'POST', body: { product_id: productId } }),
    unlinkOffer: (id: number) => http<Offer>(`/admin/offers/${id}/unlink`, { method: 'POST' }),
    createProduct: (id: number, categoryId: number) =>
      http<OfferCreateProductResult>(`/admin/offers/${id}/create-product`, {
        method: 'POST',
        body: { category_id: categoryId },
      }),
  }
}
