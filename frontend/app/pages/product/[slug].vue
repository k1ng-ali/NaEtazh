<script setup lang="ts">
import { computed, ref } from 'vue'
import QuantityStepper from '~/features/cart/components/QuantityStepper.vue'
import { useCartStore } from '~/features/cart/store'
import { useAddToCart } from '~/features/cart/useAddToCart'
import { useCatalogApi } from '~/features/catalog/api'
import { AVAILABILITY } from '~/features/checkout/labels'
import { formatPrice, formatQuantity } from '~/shared/lib/format'
import { useMediaUrl } from '~/shared/lib/media'

const route = useRoute()
const api = useCatalogApi()
const cart = useCartStore()
const addToCart = useAddToCart()
const mediaUrl = useMediaUrl()

const slug = computed(() => String(route.params.slug))
const { data: product, error } = await useAsyncData(`product-${slug.value}`, () => api.getProduct(slug.value))
if (error.value) {
  throw createError({ statusCode: 404, statusMessage: 'Товар не найден', fatal: true })
}

const quantity = ref(1)
const activeImage = ref(0)
const justAdded = ref(false)

const images = computed(() => (product.value?.images ?? []).map(mediaUrl))
const availability = computed(() => (product.value ? AVAILABILITY[product.value.availability] : null))
const total = computed(() => (product.value ? Number(product.value.price) * quantity.value : 0))
const attributes = computed(() => Object.entries(product.value?.attributes ?? {}))

function add() {
  if (!product.value) return
  addToCart(product.value, quantity.value)
  justAdded.value = true
}

useHead(() => ({
  title: product.value ? `${product.value.name} | СтройБаза97` : 'СтройБаза97',
  meta: [{ name: 'description', content: product.value?.description?.slice(0, 160) ?? product.value?.name ?? '' }],
}))
</script>

<template>
  <div v-if="product" class="container product">
    <NuxtLink to="/catalog" class="muted product__back">← Каталог</NuxtLink>

    <div class="product__layout">
      <section class="product__gallery">
        <div class="product__photo">
          <img v-if="images.length" :src="images[activeImage]" :alt="product.name">
          <span v-else class="muted">Фото скоро появится</span>
        </div>
        <div v-if="images.length > 1" class="product__thumbs">
          <button
            v-for="(url, index) in images"
            :key="url"
            class="product__thumb"
            :class="{ 'is-active': index === activeImage }"
            type="button"
            :aria-label="`Фото ${index + 1}`"
            @click="activeImage = index"
          >
            <img :src="url" alt="">
          </button>
        </div>
      </section>

      <section class="product__info">
        <h1 class="product__name">{{ product.name }}</h1>
        <span v-if="availability" class="badge" :class="`badge--${availability.modifier}`">{{ availability.label }}</span>
        <p class="product__price">
          {{ formatPrice(product.price) }} <span class="muted">/ {{ product.unit }}</span>
        </p>

        <div v-if="product.availability !== 'unavailable'" class="product__buy card">
          <div class="product__qty">
            <QuantityStepper v-model="quantity" :unit="product.unit" />
            <span class="product__total">{{ formatPrice(total) }}</span>
          </div>
          <button class="btn btn--block btn--large" type="button" @click="add">Добавить в корзину</button>
          <p v-if="justAdded" class="product__added">
            В корзине {{ cart.quantityOf(product.id) }} {{ product.unit }}.
            <NuxtLink to="/cart" class="product__link">Перейти в корзину</NuxtLink>
          </p>
        </div>
        <p v-else class="muted">Сейчас нет в наличии.</p>

        <dl v-if="attributes.length || product.weight_kg || product.length_mm" class="product__specs">
          <template v-for="[key, value] in attributes" :key="key">
            <dt>{{ key }}</dt>
            <dd>{{ value }}</dd>
          </template>
          <template v-if="product.weight_kg">
            <dt>Вес</dt>
            <dd>{{ formatQuantity(product.weight_kg) }} кг</dd>
          </template>
          <template v-if="product.length_mm">
            <dt>Длина</dt>
            <dd>{{ product.length_mm }} мм</dd>
          </template>
        </dl>

        <p v-if="product.description" class="product__description">{{ product.description }}</p>
      </section>
    </div>
  </div>
</template>

<style scoped lang="scss">
.product {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__back {
    align-self: flex-start;
  }

  &__layout {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  &__gallery {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__photo {
    display: flex;
    align-items: center;
    justify-content: center;
    aspect-ratio: 1;
    overflow: hidden;
    border-radius: var(--radius-card);
    background: var(--color-surface);

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }

  &__thumbs {
    display: flex;
    gap: 8px;
    overflow-x: auto;
  }

  &__thumb {
    flex-shrink: 0;
    width: 64px;
    height: 64px;
    padding: 0;
    overflow: hidden;
    border: 1.5px solid var(--color-line);
    border-radius: 8px;
    background: var(--color-surface);
    cursor: pointer;

    &.is-active {
      border-color: var(--color-text);
    }

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }

  &__info {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  &__name {
    font-size: 22px;
    font-weight: 700;
  }

  &__price {
    font-size: 26px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;

    .muted {
      font-size: 16px;
      font-weight: 400;
    }
  }

  &__buy {
    display: flex;
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }

  &__qty {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  &__total {
    font-size: 18px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  &__added {
    font-size: 15px;
  }

  &__link {
    font-weight: 600;
    text-decoration: underline;
  }

  &__specs {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr);
    gap: 8px 16px;
    width: 100%;
    margin: 8px 0 0;

    dt {
      color: var(--color-text-muted);
    }

    dd {
      margin: 0;
    }
  }

  &__description {
    white-space: pre-line;
  }
}

/* Десктоп: фото слева, покупка справа */
@media (min-width: 1024px) {
  .product {
    &__layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 40px;
      align-items: start;
    }

    &__gallery {
      position: sticky;
      top: 96px;
    }

    &__name {
      font-size: 30px;
    }

    &__buy {
      max-width: 420px;
    }
  }
}
</style>
