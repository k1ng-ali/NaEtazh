<script setup lang="ts">
import { computed } from 'vue'
import { formatPrice } from '~/shared/lib/format'
import { useMediaUrl } from '~/shared/lib/media'
import type { Product } from '../types'

const props = defineProps<{
  product: Product
  // Сколько уже в корзине
  inCart: number
}>()

const emit = defineEmits<{
  (e: 'add', product: Product): void
}>()

const mediaUrl = useMediaUrl()
const price = computed(() => formatPrice(props.product.price))
const image = computed(() => (props.product.images[0] ? mediaUrl(props.product.images[0]) : null))
const link = computed(() => `/product/${props.product.slug}`)
</script>

<template>
  <article class="card">
    <NuxtLink :to="link" class="card__image" tabindex="-1" aria-hidden="true">
      <img v-if="image" :src="image" :alt="product.name" loading="lazy">
      <span v-else>Фото</span>
    </NuxtLink>
    <div class="card__body">
      <NuxtLink :to="link" class="card__name">{{ product.name }}</NuxtLink>
      <div class="card__bottom">
        <p class="card__price">
          {{ price }} <span class="card__unit">/ {{ product.unit }}</span>
        </p>
        <button
          class="card__add"
          :class="{ 'is-added': inCart }"
          type="button"
          :aria-label="`Добавить в корзину: ${product.name}`"
          @click="emit('add', product)"
        >
          {{ inCart ? `В корзине ${inCart}` : 'В корзину' }}
        </button>
      </div>
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
    justify-content: space-between;
    gap: 8px;
    min-width: 0;
  }

  &__name {
    font-size: 15px;
    font-weight: 600;

    &:hover {
      text-decoration: underline;
    }
  }

  &__bottom {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
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

  &__add {
    min-height: 40px;
    padding: 0 14px;
    border: 1.5px solid var(--color-text);
    border-radius: var(--radius-control);
    background: var(--color-text);
    color: var(--color-inverse);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;

    &.is-added {
      background: var(--color-surface);
      color: var(--color-text);
    }
  }
}

/* На десктопе карточка вертикальная: фото крупнее */
@media (min-width: 1024px) {
  .card {
    flex-direction: column;

    &__image {
      width: 100%;
      height: 180px;
    }
  }
}
</style>
