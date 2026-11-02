<script setup lang="ts">
import { formatPrice } from '~/shared/lib/format'
import type { Quote } from '../types'

defineProps<{
  quote: Quote | null
  isQuoting: boolean
}>()
</script>

<template>
  <section class="summary card" :class="{ 'is-loading': isQuoting }" aria-live="polite">
    <template v-if="quote">
      <div class="summary__row">
        <span>Товары</span>
        <span>{{ formatPrice(quote.goods_total) }}</span>
      </div>
      <div v-for="service in quote.services" :key="service.type" class="summary__row">
        <span>{{ service.name }}</span>
        <span>{{ Number(service.price) ? formatPrice(service.price) : 'Бесплатно' }}</span>
      </div>
      <p v-if="quote.services_unknown" class="muted summary__note">Стоимость доставки сообщит менеджер</p>
      <p v-else-if="quote.weight_unknown && quote.services.some((item) => item.type === 'lifting')" class="muted summary__note">
        Вес части товаров неизвестен, цену подъёма уточнит менеджер
      </p>
      <div class="summary__row summary__total">
        <span>Итого</span>
        <span>{{ formatPrice(quote.total) }}</span>
      </div>
      <p class="muted summary__note">Оплата при получении наличными</p>
    </template>
    <p v-else class="muted">Считаем…</p>
    <slot />
  </section>
</template>

<style scoped lang="scss">
.summary {
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: opacity 0.15s ease;

  &.is-loading {
    opacity: 0.6;
  }

  &__row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-variant-numeric: tabular-nums;
  }

  &__total {
    padding-top: 10px;
    border-top: 1px solid var(--color-line);
    font-size: 20px;
    font-weight: 700;
  }

  &__note {
    font-size: 14px;
  }
}
</style>
