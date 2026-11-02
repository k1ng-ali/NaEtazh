import { useAdminHttp } from '../shared/http'
import type {
  AdminCategory,
  AdminProduct,
  CategoryPayload,
  ProductFilters,
  ProductPayload,
  ProductRowList,
  StockPayload,
  Warehouse,
} from './types'

export const useAdminCatalogApi = () => {
  const http = useAdminHttp()

  return {
    listCategories: () => http<AdminCategory[]>('/admin/categories/'),
    createCategory: (payload: CategoryPayload) =>
      http<AdminCategory>('/admin/categories/', { method: 'POST', body: payload }),
    updateCategory: (id: number, payload: CategoryPayload) =>
      http<AdminCategory>(`/admin/categories/${id}`, { method: 'PATCH', body: payload }),
    deleteCategory: (id: number) => http<void>(`/admin/categories/${id}`, { method: 'DELETE' }),

    listProducts: (filters: ProductFilters = {}) => http<ProductRowList>('/admin/products/', { query: filters }),
    getProduct: (id: number) => http<AdminProduct>(`/admin/products/${id}`),
    createProduct: (payload: ProductPayload) =>
      http<AdminProduct>('/admin/products/', { method: 'POST', body: payload }),
    updateProduct: (id: number, payload: ProductPayload) =>
      http<AdminProduct>(`/admin/products/${id}`, { method: 'PATCH', body: payload }),
    uploadImage: (id: number, file: File) => {
      const body = new FormData()
      body.append('file', file)
      return http<AdminProduct>(`/admin/products/${id}/images`, { method: 'POST', body })
    },
    setStock: (id: number, payload: StockPayload) =>
      http<AdminProduct>(`/admin/products/${id}/stock`, { method: 'PUT', body: payload }),

    listWarehouses: () => http<Warehouse[]>('/admin/warehouses/'),
  }
}
