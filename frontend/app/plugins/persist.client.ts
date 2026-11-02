import { useCartStore } from '~/features/cart/store'
import { useCookieStore } from '~/features/cookies/store'
import { useLocationStore } from '~/features/location/store'

// Корзину, корпус и выбор cookie читаем из localStorage один раз при открытии сайта
export default defineNuxtPlugin(() => {
  useLocationStore().hydrate()
  useCartStore().hydrate()
  useCookieStore().hydrate()
})
