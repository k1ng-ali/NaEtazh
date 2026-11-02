<script setup lang="ts">
import { computed } from 'vue'
import { formatPrice } from '~/shared/lib/format'
import { useMediaUrl } from '~/shared/lib/media'
import type { Product } from '../types'

const props = defineProps<{
  product: Product
}>()

const mediaUrl = useMediaUrl()
const price = computed(() => formatPrice(props.product.price))
const image = computed(() => (props.product.images[0] ? mediaUrl(props.product.images[0]) : null))
</script>

<template>
  <article class="card">
    <div class="card__image">
      <img v-if="image" :src="image" :alt="product.name" loading="lazy">
      <span v-else>Фото</span>
    </div>
    <div class="card__body">
      <h3 class="card__name">{{ product.name }}</h3>
      <p class="card__price">
        {{ price }} <span class="card__unit">/ {{ product.unit }}</span>
      </p>
    </div>
  </article>
</template>

<style scoped lang="scss">
.card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--color-surface);
  border-radius: var(--radius-card);

  &__image {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    width: 88px;
    height: 88px;
    overflow: hidden;
    background: var(--color-bg);
    border-radius: 8px;
    color: var(--color-text-muted);
    font-size: 14px;

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }

  &__body {
    display: flex;
    flex: 1;
    flex-direction: column;
    gap: 6px;
    min-width: 0;
  }

  &__name {
    font-size: 15px;
    font-weight: 600;
  }

  &__price {
    font-size: 18px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  &__unit {
    color: var(--color-text-muted);
    font-size: 14px;
    font-weight: 400;
  }
}
</style>
