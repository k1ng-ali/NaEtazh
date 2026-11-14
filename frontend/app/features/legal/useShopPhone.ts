import { computed } from 'vue'
import { useServicesApi } from '~/features/services/api'
import { SELLER } from '~/shared/lib/legal'

// Телефон по заказам: тот же, что владелец задал в разделе «Услуги»
export async function useShopPhone() {
  const api = useServicesApi()
  const { data } = await useAsyncData('shop-contacts', () => api.getContacts())
  return computed(() => data.value?.phone ?? SELLER.ordersPhone)
}
