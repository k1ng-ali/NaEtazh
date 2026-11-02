import type { Product } from '~/features/catalog/types'
import { useCartStore } from './store'

// Добавление из каталога и карточки товара одинаковое
export const useAddToCart = () => {
  const cart = useCartStore()

  return (product: Product, quantity = 1) =>
    cart.add(
      {
        product_id: product.id,
        slug: product.slug,
        name: product.name,
        unit: product.unit,
        price: product.price,
        image: product.images[0] ?? null,
      },
      quantity,
    )
}
