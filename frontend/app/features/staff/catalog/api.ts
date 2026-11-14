import { useStaffHttp } from '../shared/http'
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
  const http = useStaffHttp()

  return {
    listCategories: () => http<AdminCategory[]>('/manager/categories/'),
    createCategory: (payload: CategoryPayload) =>
      http<AdminCategory>('/manager/categories/', { method: 'POST', body: payload }),
    updateCategory: (id: number, payload: CategoryPayload) =>
      http<AdminCategory>(`/manager/categories/${id}`, { method: 'PATCH', body: payload }),
    deleteCategory: (id: number) => http<void>(`/manager/categories/${id}`, { method: 'DELETE' }),
    uploadCategoryImage: (id: number, file: File) => {
      const body = new FormData()
      body.append('file', file)
      return http<AdminCategory>(`/manager/categories/${id}/image`, { method: 'POST', body })
    },
    deleteCategoryImage: (id: number) =>
      http<AdminCategory>(`/manager/categories/${id}/image`, { method: 'DELETE' }),

    listProducts: (filters: ProductFilters = {}) => http<ProductRowList>('/manager/products/', { query: filters }),
    getProduct: (id: number) => http<AdminProduct>(`/manager/products/${id}`),
    createProduct: (payload: ProductPayload) =>
      http<AdminProduct>('/manager/products/', { method: 'POST', body: payload }),
    updateProduct: (id: number, payload: ProductPayload) =>
      http<AdminProduct>(`/manager/products/${id}`, { method: 'PATCH', body: payload }),
    uploadImage: (id: number, file: File) => {
      const body = new FormData()
      body.append('file', file)
      return http<AdminProduct>(`/manager/products/${id}/images`, { method: 'POST', body })
    },
    setStock: (id: number, payload: StockPayload) =>
      http<AdminProduct>(`/manager/products/${id}/stock`, { method: 'PUT', body: payload }),

    listWarehouses: () => http<Warehouse[]>('/manager/warehouses/'),
  }
}
