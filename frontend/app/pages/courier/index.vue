<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useCourierApi } from '~/features/courier/api'
import type { CourierOrderRow } from '~/features/courier/types'
import { DELIVERY_SLOT, LIFTING, ORDER_STATUS } from '~/features/checkout/labels'
import { errorMessage } from '~/features/staff/shared/errors'
import { formatPrice } from '~/shared/lib/format'

definePageMeta({ layout: 'courier', middleware: 'staff', roles: ['courier'] })
useHead({ title: 'Доставки | Строй База' })

// Менеджер может назначить заказ в любой момент, список обновляется сам
const REFRESH_MS = 60_000

const api = useCourierApi()
const orders = ref<CourierOrderRow[] | null>(null)
const errorText = ref('')

const isoDate = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
const dateFormat = new Intl.DateTimeFormat('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })

const groups = computed(() => {
  const today = new Date()
  const tomorrow = new Date(today)
  tomorrow.setDate(today.getDate() + 1)
  const keys = { today: isoDate(today), tomorrow: isoDate(tomorrow) }

  const result = new Map<string, { title: string; items: CourierOrderRow[] }>()
  const push = (key: string, title: string, order: CourierOrderRow) => {
    if (!result.has(key)) result.set(key, { title, items: [] })
    result.get(key)!.items.push(order)
  }
  for (const order of orders.value ?? []) {
    if (order.status === 'delivered') push('done', 'Отвезено сегодня', order)
    // Заказ в пути показываем первым, даже если дата не сегодня
    else if (order.status === 'in_delivery') push('active', 'В пути', order)
    else if (!order.planned_date || order.planned_date <= keys.today) push('today', 'Сегодня', order)
    else if (order.planned_date === keys.tomorrow) push('tomorrow', 'Завтра', order)
    else push(order.planned_date, dateFormat.format(new Date(`${order.planned_date}T00:00:00`)), order)
  }
  const order = ['active', 'today', 'tomorrow']
  return [...result.entries()]
    .sort(([a], [b]) => {
      const rank = (key: string) => (key === 'done' ? 99 : order.includes(key) ? order.indexOf(key) : 10)
      return rank(a) - rank(b) || a.localeCompare(b)
    })
    .map(([key, group]) => ({ key, ...group }))
})

async function load() {
  try {
    orders.value = await api.listOrders()
    errorText.value = ''
  } catch (error) {
    errorText.value = errorMessage(error, 'Не удалось загрузить доставки')
  }
}

let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  load()
  timer = setInterval(load, REFRESH_MS)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="list">
    <p v-if="errorText" class="a-error" role="alert">{{ errorText }}</p>
    <p v-else-if="!orders" class="a-muted">Загружаем…</p>
    <div v-else-if="!orders.length" class="a-card a-empty">
      Доставок пока нет. Когда менеджер назначит заказ, он появится здесь.
    </div>

    <section v-for="group in groups" :key="group.key" class="group">
      <h2 class="group__title">{{ group.title }} <span class="a-muted">{{ group.items.length }}</span></h2>
      <NuxtLink
        v-for="order in group.items"
        :key="order.id"
        :to="`/courier/orders/${order.id}`"
        class="a-card card"
        :class="{ 'is-done': order.status === 'delivered', 'is-active': order.status === 'in_delivery' }"
      >
        <div class="card__head">
          <strong>№ {{ order.id }}</strong>
          <span v-if="order.planned_slot" class="a-badge">{{ DELIVERY_SLOT[order.planned_slot] }}</span>
          <span v-if="order.status !== 'confirmed'" class="a-badge" :class="order.status === 'delivered' ? 'a-badge--success' : 'a-badge--warning'">
            {{ ORDER_STATUS[order.status] }}
          </span>
        </div>
        <span class="card__address">{{ order.address }}</span>
        <span class="a-muted">{{ LIFTING[order.lifting_type] }}</span>
        <span class="card__total">Получить {{ formatPrice(order.total) }}</span>
      </NuxtLink>
    </section>
  </div>
</template>

<style scoped lang="scss">
.list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.group {
  display: flex;
  flex-direction: column;
  gap: 10px;

  &__title {
    font-size: 18px;
    font-weight: 700;

    &::first-letter {
      text-transform: uppercase;
    }
  }
}

.card {
  gap: 6px;

  &.is-active {
    border: 2px solid var(--color-text);
  }

  &.is-done {
    opacity: 0.6;
  }

  &__head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }

  &__address {
    font-size: 17px;
    font-weight: 600;
  }

  &__total {
    font-size: 17px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }
}
</style>
