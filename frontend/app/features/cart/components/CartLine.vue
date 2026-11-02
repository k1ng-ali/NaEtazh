<script setup lang="ts">
import { computed } from 'vue'
import { AVAILABILITY } from '~/features/checkout/labels'
import { formatPrice, formatQuantity } from '~/shared/lib/format'
import { useMediaUrl } from '~/shared/lib/media'
import type { CartItem, QuoteLine } from '../types'
import QuantityStepper from './QuantityStepper.vue'

const props = defineProps<{
  item: CartItem
  // Расчёт сервера, пока его нет — показываем снимок из корзины
  line: QuoteLine | null
}>()

const emit = defineEmits<{
  (e: 'quantity', value: number): void
  (e: 'remove'): void
}>()

const mediaUrl = useMediaUrl()
const image = computed(() => (props.item.image ? mediaUrl(props.item.image) : null))
const total = computed(() => props.line?.total ?? Number(props.item.price) * props.item.quantity)
const availability = computed(() => (props.line ? AVAILABILITY[props.line.availability] : null))
</script>

<template>
  <article class="line">
    <NuxtLink :to="`/product/${item.slug}`" class="line__image" tabindex="-1" aria-hidden="true">
      <img v-if="image" :src="image" alt="">
    </NuxtLink>
    <div class="line__body">
      <NuxtLink :to="`/product/${item.slug}`" class="line__name">{{ item.name }}</NuxtLink>
      <span class="muted">{{ formatPrice(item.price) }} / {{ item.unit }}</span>
      <span v-if="availability" class="badge" :class="`badge--${availability.modifier}`">{{ availability.label }}</span>
      <template v-if="line?.availability === 'unavailable'">
        <p v-if="Number(line.available_quantity) > 0" class="error-text line__note">
          Можно заказать не больше {{ formatQuantity(line.available_quantity) }} {{ item.unit }}
        </p>
        <p v-else class="error-text line__note">Закончился. Удалите товар, чтобы оформить заказ</p>
      </template>
      <p v-if="line?.too_long_for_lift" class="line__note">Не помещается в грузовой лифт, поднимать по лестнице</p>
    </div>
    <div class="line__controls">
      <QuantityStepper :model-value="item.quantity" :unit="item.unit" @update:model-value="emit('quantity', $event)" />
      <span class="line__total">{{ formatPrice(total) }}</span>
      <button class="line__remove" type="button" @click="emit('remove')">Удалить</button>
    </div>
  </article>
</template>

<style scoped lang="scss">
.line {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 10px 12px;
  padding: 14px 0;

  & + & {
    border-top: 1px solid var(--color-line);
  }

  &__image {
    width: 72px;
    height: 72px;
    overflow: hidden;
    border-radius: 8px;
    background: var(--color-bg);

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }

  &__body {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    min-width: 0;
  }

  &__name {
    font-weight: 600;
  }

  &__note {
    font-size: 14px;
  }

  &__controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 16px;
    grid-column: 1 / -1;
  }

  &__total {
    margin-left: auto;
    font-size: 17px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  &__remove {
    min-height: var(--tap-size);
    padding: 0 4px;
    border: 0;
    background: transparent;
    color: var(--color-text-muted);
    text-decoration: underline;
    cursor: pointer;
  }
}

@media (min-width: 768px) {
  .line {
    grid-template-columns: 88px minmax(0, 1fr) auto;
    align-items: center;

    &__image {
      width: 88px;
      height: 88px;
    }

    &__controls {
      grid-column: auto;
      flex-wrap: nowrap;
    }

    &__total {
      min-width: 100px;
      text-align: right;
    }
  }
}
</style>
