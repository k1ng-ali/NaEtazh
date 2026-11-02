import { useCartStore } from '~/features/cart/store'
import { useLocationStore } from '~/features/location/store'

// Корзину и корпус читаем из localStorage один раз при открытии сайта
export default defineNuxtPlugin(() => {
  useLocationStore().hydrate()
  useCartStore().hydrate()
})
