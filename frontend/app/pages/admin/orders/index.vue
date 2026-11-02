<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ORDER_STATUS, DELIVERY_SLOT } from '~/features/checkout/labels'
import type { OrderStatus } from '~/features/checkout/types'
import { useAdminOrdersApi } from '~/features/admin/orders/api'
import OrderStatusBadge from '~/features/admin/orders/components/OrderStatusBadge.vue'
import type { OrderRowList } from '~/features/admin/orders/types'
import { errorMessage } from '~/features/admin/shared/errors'
import { formatDateTime, formatPrice } from '~/shared/lib/format'

definePageMeta({ layout: 'admin', middleware: 'admin' })
useHead({ title: 'Заказы | Админка' })

const PAGE_SIZE = 50
// Новые заказы появляются без перезагрузки страницы
const REFRESH_MS = 60_000

const api = useAdminOrdersApi()
const route = useRoute()
const router = useRouter()

const status = computed(() => (typeof route.query.status === 'string' ? (route.query.status as OrderStatus) : undefined))
const skip = computed(() => Number(route.query.skip) || 0)
const search = ref(typeof route.query.search === 'string' ? route.query.search : '')
const data = ref<OrderRowList | null>(null)
const errorText = ref('')

const page = computed(() => Math.floor(skip.value / PAGE_SIZE) + 1)
const pages = computed(() => Math.max(1, Math.ceil((data.value?.total ?? 0) / PAGE_SIZE)))
const dateFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' })

function setQuery(values: Record<string, string | number | undefined>) {
  const query = { ...route.query, ...values }
  for (const key of Object.keys(query)) {
    if (query[key] === undefined || query[key] === '' || query[key] === 0) delete query[key]
  }
  router.replace({ query })
}

async function load() {
  try {
    data.value = await api.listOrders({
      status: status.value,
      search: search.value.trim() || undefined,
      skip: skip.value,
      limit: PAGE_SIZE,
    })
    errorText.value = ''
  } catch (error) {
    errorText.value = errorMessage(error, 'Не удалось загрузить заказы')
  }
}

const when = (row: { delivery_date: string | null; delivery_slot: keyof typeof DELIVERY_SLOT | null }) =>
  [row.delivery_date ? dateFormat.format(new Date(`${row.delivery_date}T00:00:00`)) : 'Скорее', row.delivery_slot && DELIVERY_SLOT[row.delivery_slot].split(',')[0]?.toLowerCase()]
    .filter(Boolean)
    .join(', ')

let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, (value) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => setQuery({ search: value.trim(), skip: undefined }), 300)
})
watch(() => route.query, load)

let refreshTimer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  load()
  refreshTimer = setInterval(load, REFRESH_MS)
})
onBeforeUnmount(() => {
  clearInterval(refreshTimer)
  clearTimeout(searchTimer)
})
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <div>
        <h1 class="a-title">Заказы</h1>
        <p class="a-muted">{{ data ? `Всего ${data.total}` : 'Загружаем…' }}</p>
      </div>
    </div>

    <div class="filters">
      <input v-model="search" class="a-input" type="search" placeholder="Номер, имя или телефон" aria-label="Поиск заказов">
      <select
        class="a-select"
        aria-label="Статус"
        :value="status ?? ''"
        @change="setQuery({ status: ($event.target as HTMLSelectElement).value, skip: undefined })"
      >
        <option value="">Все статусы</option>
        <option v-for="(label, value) in ORDER_STATUS" :key="value" :value="value">{{ label }}</option>
      </select>
    </div>

    <p v-if="errorText" class="a-error" role="alert">{{ errorText }}</p>
    <div v-else-if="data && !data.items.length" class="a-card a-empty">
      Заказов пока нет. Они появятся здесь, а менеджеру придёт сообщение в Telegram.
    </div>
    <div v-else-if="data" class="a-card orders">
      <table class="a-table orders__table">
        <thead>
          <tr>
            <th>№</th>
            <th>Создан</th>
            <th>Покупатель</th>
            <th>Адрес</th>
            <th>Когда</th>
            <th class="a-table__num">Сумма</th>
            <th>Статус</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data.items" :key="row.id" class="orders__row" @click="navigateTo(`/admin/orders/${row.id}`)">
            <td><NuxtLink :to="`/admin/orders/${row.id}`" class="orders__number">{{ row.id }}</NuxtLink></td>
            <td class="a-muted">{{ formatDateTime(row.created_at) }}</td>
            <td>
              {{ row.customer_name }}
              <span class="a-muted orders__phone">{{ row.customer_phone }}</span>
            </td>
            <td class="orders__address">{{ row.address }}</td>
            <td class="a-muted">{{ when(row) }}</td>
            <td class="a-table__num">{{ formatPrice(row.total) }}</td>
            <td>
              <OrderStatusBadge :status="row.status" />
              <span v-if="row.has_supplier_items && ['new', 'checking'].includes(row.status)" class="a-muted orders__supplier">
                есть товары партнёра
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      <ul class="orders__list">
        <li v-for="row in data.items" :key="row.id">
          <NuxtLink :to="`/admin/orders/${row.id}`" class="orders__item">
            <div class="orders__item-head">
              <strong>№ {{ row.id }} · {{ formatPrice(row.total) }}</strong>
              <OrderStatusBadge :status="row.status" />
            </div>
            <span>{{ row.customer_name }}, {{ row.customer_phone }}</span>
            <span class="a-muted">{{ row.address }}</span>
            <span class="a-muted">{{ when(row) }} · создан {{ formatDateTime(row.created_at) }}</span>
          </NuxtLink>
        </li>
      </ul>
    </div>

    <div v-if="pages > 1" class="a-pager">
      <button class="a-btn a-btn--ghost" type="button" :disabled="page <= 1" @click="setQuery({ skip: skip - PAGE_SIZE })">
        Назад
      </button>
      <span class="a-muted">Страница {{ page }} из {{ pages }}</span>
      <button class="a-btn a-btn--ghost" type="button" :disabled="page >= pages" @click="setQuery({ skip: skip + PAGE_SIZE })">
        Дальше
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 8px;
}

.orders {
  gap: 0;
  padding: 0;

  &__table {
    display: none;
  }

  &__list {
    margin: 0;
    padding: 0;
    list-style: none;

    li + li {
      border-top: 1px solid var(--color-line);
    }
  }

  &__item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 14px 16px;
  }

  &__item-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  &__phone,
  &__supplier {
    display: block;
    font-size: 13px;
  }

  &__number {
    font-weight: 700;
  }
}

@media (min-width: 768px) {
  .filters {
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  }
}

@media (min-width: 1024px) {
  .orders {
    padding: 4px 8px;

    &__table {
      display: table;
    }

    &__list {
      display: none;
    }

    &__row {
      cursor: pointer;

      &:hover td {
        background: var(--color-bg);
      }
    }

    &__address {
      max-width: 280px;
    }
  }
}
</style>
