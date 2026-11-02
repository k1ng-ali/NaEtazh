<script setup lang="ts">
import { computed, ref } from 'vue'
import { formatPrice } from '~/shared/lib/format'
import type { Dashboard } from '../types'

const props = defineProps<{
  days: Dashboard['days']
}>()

const dayFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' })
const label = (value: string) => dayFormat.format(new Date(`${value}T00:00:00`))

// Одна величина — выручка; число заказов в подсказке и таблице, без второй оси
const max = computed(() => Math.max(...props.days.map((day) => Number(day.revenue)), 0))
const bars = computed(() =>
  props.days.map((day) => ({
    ...day,
    height: max.value ? (Number(day.revenue) / max.value) * 100 : 0,
  })),
)
// Подписи дат не налезают друг на друга: при длинном периоде показываем каждую n-ю
const labelStep = computed(() => Math.ceil(props.days.length / 10))
const hovered = ref<number | null>(null)
</script>

<template>
  <figure class="chart">
    <figcaption class="chart__caption">
      <span class="a-subtitle">Выручка по дням</span>
      <span class="a-muted">по доставленным заказам</span>
    </figcaption>

    <div class="chart__plot" @mouseleave="hovered = null">
      <div
        v-for="(bar, index) in bars"
        :key="bar.date"
        class="chart__slot"
        tabindex="0"
        :aria-label="`${label(bar.date)}: ${formatPrice(bar.revenue)}, заказов ${bar.orders}`"
        @mouseenter="hovered = index"
        @focus="hovered = index"
        @blur="hovered = null"
      >
        <div class="chart__bar" :class="{ 'is-empty': !bar.height }" :style="{ height: `${Math.max(bar.height, 1)}%` }" />
        <div v-if="hovered === index" class="chart__tip" :class="{ 'is-right': index > bars.length / 2 }">
          <strong>{{ label(bar.date) }}</strong>
          <span>{{ formatPrice(bar.revenue) }}</span>
          <span class="a-muted">заказов: {{ bar.orders }}</span>
        </div>
        <span class="chart__label">{{ index % labelStep === 0 ? label(bar.date) : '' }}</span>
      </div>
    </div>

    <details class="chart__table">
      <summary class="a-muted">Показать таблицей</summary>
      <table class="a-table">
        <thead>
          <tr>
            <th>День</th>
            <th class="a-table__num">Заказов</th>
            <th class="a-table__num">Выручка</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="day in days" :key="day.date">
            <td>{{ label(day.date) }}</td>
            <td class="a-table__num">{{ day.orders }}</td>
            <td class="a-table__num">{{ formatPrice(day.revenue) }}</td>
          </tr>
        </tbody>
      </table>
    </details>
  </figure>
</template>

<style scoped lang="scss">
.chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;

  &__caption {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 4px 10px;
  }

  &__plot {
    display: flex;
    align-items: flex-end;
    gap: 2px;
    height: 180px;
    padding-bottom: 22px;
    border-bottom: 1px solid var(--color-line);
  }

  &__slot {
    position: relative;
    display: flex;
    flex: 1;
    flex-direction: column;
    justify-content: flex-end;
    height: 100%;
    min-width: 0;
    outline-offset: 2px;
    cursor: default;
  }

  &__bar {
    width: 100%;
    max-width: 28px;
    margin: 0 auto;
    border-radius: 4px 4px 0 0;
    background: var(--color-text);

    &.is-empty {
      background: var(--color-line);
    }
  }

  &__slot:hover &__bar:not(.is-empty),
  &__slot:focus-visible &__bar:not(.is-empty) {
    opacity: 0.75;
  }

  &__label {
    position: absolute;
    bottom: -20px;
    left: 50%;
    color: var(--color-text-muted);
    font-size: 11px;
    white-space: nowrap;
    transform: translateX(-50%);
  }

  &__tip {
    position: absolute;
    bottom: calc(100% + 4px);
    left: 0;
    z-index: 2;
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px 10px;
    border: 1px solid var(--color-line);
    border-radius: 8px;
    background: var(--color-surface);
    font-size: 13px;
    white-space: nowrap;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.12);
    pointer-events: none;

    &.is-right {
      right: 0;
      left: auto;
    }
  }

  &__table summary {
    cursor: pointer;
    font-size: 14px;
  }
}
</style>
