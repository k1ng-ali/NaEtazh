import { useHttp } from '~/shared/api/http'
import type { Category, ProductDetail, ProductFilters, ProductList } from './types'

export const useCatalogApi = () => {
  const http = useHttp()

  return {
    listCategories: () => http<Category[]>('/categories/'),
    listProducts: (filters: ProductFilters = {}) => http<ProductList>('/products/', { query: filters }),
    getProduct: (slug: string) => http<ProductDetail>(`/products/${encodeURIComponent(slug)}`),
  }
}
