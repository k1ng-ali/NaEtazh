import { onBeforeUnmount, onMounted, watch } from 'vue'
import { useLocationStore } from '~/features/location/store'
import { useCartStore } from './store'

// Пересчитывает корзину на сервере при любом изменении, с небольшой паузой между нажатиями «+»
export const useQuoteSync = () => {
  const cart = useCartStore()
  const location = useLocationStore()
  let timer: ReturnType<typeof setTimeout> | undefined

  const schedule = () => {
    clearTimeout(timer)
    timer = setTimeout(() => cart.refreshQuote(), 300)
  }

  watch(
    () => [cart.items.map((item) => `${item.product_id}:${item.quantity}`).join(), cart.liftingType, location.floor, location.building?.code],
    schedule,
  )
  onMounted(() => cart.refreshQuote())
  onBeforeUnmount(() => clearTimeout(timer))
}
