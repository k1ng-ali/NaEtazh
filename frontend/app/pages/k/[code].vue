<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { GOAL, reachGoal } from '~/features/analytics/metrika'
import { useLocationApi } from '~/features/location/api'
import { useLocationStore } from '~/features/location/store'

// Сюда ведёт QR с визитки: запоминаем корпус и сразу открываем магазин
const route = useRoute()
const api = useLocationApi()
const location = useLocationStore()
const notFound = ref(false)

onMounted(async () => {
  try {
    location.setBuilding(await api.getBuilding(String(route.params.code)))
  } catch {
    notFound.value = true
    return
  }
  reachGoal(GOAL.qrScan)
  await navigateTo('/', { replace: true })
})

useHead({ title: 'СтройБаза97', meta: [{ name: 'robots', content: 'noindex' }] })
</script>

<template>
  <div class="container qr">
    <template v-if="notFound">
      <h1 class="qr__title">Ссылка устарела</h1>
      <p class="muted">Каталог работает как обычно, адрес укажете при оформлении.</p>
      <NuxtLink to="/" class="btn">Открыть магазин</NuxtLink>
    </template>
    <p v-else class="muted">Открываем магазин…</p>
  </div>
</template>

<style scoped lang="scss">
.qr {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  padding-block: 32px;

  &__title {
    font-size: 22px;
    font-weight: 700;
  }
}
</style>
