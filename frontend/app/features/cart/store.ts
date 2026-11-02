import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import { useLocationStore } from '~/features/location/store'
import { readJson, writeJson } from '~/shared/lib/storage'
import { useCartApi } from './api'
import type { CartItem, LiftingType, Quote } from './types'

const STORAGE_KEY = 'sb97-cart'
const MAX_QUANTITY = 9999

interface SavedCart {
  items: CartItem[]
  liftingType: LiftingType
}

// Корзина хранится в браузере и переживает обрыв связи и закрытие вкладки
export const useCartStore = defineStore('cart', () => {
  const api = useCartApi()
  const location = useLocationStore()

  // ── State ──
  const items = ref<CartItem[]>([])
  const liftingType = ref<LiftingType>('none')
  // Расчёт сервера: настоящие цены, наличие, доставка и подъём
  const quote = ref<Quote | null>(null)
  const isQuoting = ref(false)
  const quoteError = ref('')

  // ── Getters ──
  const count = computed(() => items.value.length)
  const quantityOf = (productId: number) => items.value.find((item) => item.product_id === productId)?.quantity ?? 0

  // ── Actions ──
  function add(item: Omit<CartItem, 'quantity'>, quantity = 1) {
    const existing = items.value.find((row) => row.product_id === item.product_id)
    if (existing) {
      existing.quantity = Math.min(existing.quantity + quantity, MAX_QUANTITY)
    } else {
      items.value.push({ ...item, quantity })
    }
  }

  function setQuantity(productId: number, quantity: number) {
    if (quantity <= 0) return remove(productId)
    const item = items.value.find((row) => row.product_id === productId)
    if (item) item.quantity = Math.min(Math.floor(quantity), MAX_QUANTITY)
  }

  function remove(productId: number) {
    items.value = items.value.filter((item) => item.product_id !== productId)
  }

  function clear() {
    items.value = []
    quote.value = null
  }

  function payload() {
    return {
      items: items.value.map((item) => ({ product_id: item.product_id, quantity: item.quantity })),
      building_code: location.building?.code ?? null,
      floor: location.floor,
      lifting_type: liftingType.value,
    }
  }

  let requestId = 0
  async function refreshQuote() {
    if (!items.value.length) {
      quote.value = null
      return
    }
    // Ответ на старый запрос не должен перетереть свежий расчёт
    const current = ++requestId
    isQuoting.value = true
    quoteError.value = ''
    try {
      const result = await api.quote(payload())
      if (current !== requestId) return
      quote.value = result
      // Снятые с продажи товары убираем, цены обновляем по серверу
      if (result.removed_product_ids.length) {
        items.value = items.value.filter((item) => !result.removed_product_ids.includes(item.product_id))
      }
      for (const line of result.lines) {
        const item = items.value.find((row) => row.product_id === line.product_id)
        if (item) item.price = line.unit_price
      }
    } catch {
      if (current === requestId) quoteError.value = 'Не удалось пересчитать корзину. Проверьте интернет'
    } finally {
      if (current === requestId) isQuoting.value = false
    }
  }

  function hydrate() {
    const saved = readJson<Partial<SavedCart>>(STORAGE_KEY, {})
    items.value = Array.isArray(saved.items) ? saved.items : []
    liftingType.value = saved.liftingType ?? 'none'

    watch(
      [items, liftingType],
      () => writeJson(STORAGE_KEY, { items: items.value, liftingType: liftingType.value } satisfies SavedCart),
      { deep: true },
    )
  }

  return {
    items,
    liftingType,
    quote,
    isQuoting,
    quoteError,
    count,
    quantityOf,
    add,
    setQuantity,
    remove,
    clear,
    payload,
    refreshQuote,
    hydrate,
  }
})
