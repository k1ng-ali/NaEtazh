<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useDashboardApi } from '~/features/staff/dashboard/api'
import RevenueChart from '~/features/staff/dashboard/components/RevenueChart.vue'
import type { Dashboard } from '~/features/staff/dashboard/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { formatPrice } from '~/shared/lib/format'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin'] })
useHead({ title: 'Сводка | Кабинет' })

const PERIODS = [
  { days: 1, label: 'Сегодня' },
  { days: 7, label: '7 дней' },
  { days: 30, label: '30 дней' },
]

const api = useDashboardApi()
const days = ref(7)
const data = ref<Dashboard | null>(null)
const errorText = ref('')

async function load() {
  try {
    data.value = await api.getDashboard(days.value)
    errorText.value = ''
  } catch (error) {
    errorText.value = errorMessage(error, 'Не удалось загрузить сводку')
  }
}

watch(days, load)
onMounted(load)
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <h1 class="a-title">Сводка</h1>
      <div class="periods" role="tablist" aria-label="Период">
        <button
          v-for="period in PERIODS"
          :key="period.days"
          class="periods__item"
          :class="{ 'is-active': days === period.days }"
          type="button"
          role="tab"
          :aria-selected="days === period.days"
          @click="days = period.days"
        >
          {{ period.label }}
        </button>
      </div>
    </div>

    <p v-if="errorText" class="a-error" role="alert">{{ errorText }}</p>
    <p v-else-if="!data" class="a-muted">Загружаем…</p>

    <template v-else>
      <NuxtLink v-if="data.waiting" to="/manager/orders?status=new" class="a-card waiting">
        <strong>Ждут менеджера: {{ data.waiting }}</strong>
        <span class="a-muted">новые и на проверке наличия →</span>
      </NuxtLink>

      <div class="tiles">
        <div class="a-card tile">
          <span class="a-muted">Выручка</span>
          <strong class="tile__value">{{ formatPrice(data.revenue) }}</strong>
          <span class="a-muted">доставлено заказов: {{ data.delivered }}</span>
        </div>
        <div class="a-card tile">
          <span class="a-muted">Прибыль</span>
          <strong class="tile__value">{{ formatPrice(data.profit) }}</strong>
          <span class="a-muted">{{ data.profit_complete ? 'после закупки и расходов' : 'приблизительно: не все расходы указаны' }}</span>
        </div>
        <div class="a-card tile">
          <span class="a-muted">Заказов оформлено</span>
          <strong class="tile__value">{{ data.orders }}</strong>
          <span class="a-muted">отменено: {{ data.canceled }}</span>
        </div>
        <div class="a-card tile">
          <span class="a-muted">Средний чек</span>
          <strong class="tile__value">{{ formatPrice(data.avg_check) }}</strong>
          <span class="a-muted">по доставленным</span>
        </div>
      </div>

      <div class="layout">
        <section v-if="data.days.length > 1" class="a-card layout__wide">
          <RevenueChart :days="data.days" />
        </section>

        <section class="a-card">
          <h2 class="a-subtitle">Откуда заказы</h2>
          <p v-if="!data.buildings.length" class="a-muted">За период заказов нет</p>
          <table v-else class="a-table">
            <thead>
              <tr>
                <th>Дом</th>
                <th class="a-table__num">Заказов</th>
                <th class="a-table__num">Сумма</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in data.buildings" :key="row.name">
                <td>{{ row.name }}</td>
                <td class="a-table__num">{{ row.orders }}</td>
                <td class="a-table__num">{{ formatPrice(row.revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="a-card">
          <h2 class="a-subtitle">Наличные у курьеров сегодня</h2>
          <p v-if="!data.couriers_today.length" class="a-muted">Сегодня доставок ещё не было</p>
          <table v-else class="a-table">
            <thead>
              <tr>
                <th>Курьер</th>
                <th class="a-table__num">Доставок</th>
                <th class="a-table__num">Сдать</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in data.couriers_today" :key="row.name">
                <td>{{ row.name }}</td>
                <td class="a-table__num">{{ row.delivered }}</td>
                <td class="a-table__num">{{ formatPrice(row.cash) }}</td>
              </tr>
            </tbody>
          </table>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.periods {
  display: flex;
  padding: 4px;
  border-radius: var(--radius-control);
  background: var(--color-line);

  &__item {
    min-height: 36px;
    padding: 0 12px;
    border: 0;
    border-radius: 8px;
    background: transparent;
    color: var(--color-text-muted);
    font: inherit;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;

    &.is-active {
      background: var(--color-surface);
      color: var(--color-text);
    }
  }
}

.waiting {
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  border-color: var(--color-warning);
}

.tiles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.tile {
  gap: 4px;

  &__value {
    font-size: 22px;
    font-variant-numeric: tabular-nums;
  }

  .a-muted {
    font-size: 13px;
  }
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
}

@media (min-width: 1024px) {
  .tiles {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
  }

  .tile__value {
    font-size: 28px;
  }

  .layout {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    align-items: start;

    &__wide {
      grid-column: 1 / -1;
    }
  }
}
</style>
