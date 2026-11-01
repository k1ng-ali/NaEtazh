import { useHttp } from '~/shared/api/http'
import type { Category, ProductFilters, ProductList } from './types'

export const useCatalogApi = () => {
  const http = useHttp()

  return {
    listCategories: () => http<Category[]>('/categories/'),
    listProducts: (filters: ProductFilters = {}) => http<ProductList>('/products/', { query: filters }),
  }
}
