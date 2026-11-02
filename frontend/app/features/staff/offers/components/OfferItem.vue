<script setup lang="ts">
import { computed, ref } from 'vue'
import ProductPicker from '~/features/staff/catalog/components/ProductPicker.vue'
import type { ProductRow } from '~/features/staff/catalog/types'
import { formatPrice, formatQuantity } from '~/shared/lib/format'
import type { Offer } from '../types'

const props = defineProps<{
  offer: Offer
  categoryOptions: { id: number; label: string }[]
  isBusy: boolean
}>()

const emit = defineEmits<{
  (e: 'create', categoryId: number): void
  (e: 'link', product: ProductRow): void
  (e: 'unlink'): void
}>()

type Mode = 'idle' | 'create' | 'link'
const mode = ref<Mode>('idle')
const categoryId = ref<number | ''>('')

const inStock = computed(() => Number(props.offer.quantity) > 0)
// Первые два слова названия без скобок и знаков: «Унитаз (без бачка)» → «Унитаз без»
const pickerSearch = computed(() =>
  props.offer.name.replace(/[^\p{L}\p{N}\s]/gu, ' ').split(/\s+/).filter(Boolean).slice(0, 2).join(' '),
)

function create() {
  if (categoryId.value !== '') emit('create', categoryId.value)
}

function link(product: ProductRow) {
  mode.value = 'idle'
  emit('link', product)
}
</script>

<template>
  <article class="offer">
    <div class="offer__main">
      <div class="offer__thumb">
        <img v-if="offer.picture_url" :src="offer.picture_url" alt="" loading="lazy" referrerpolicy="no-referrer">
      </div>
      <div class="offer__body">
        <a v-if="offer.url" :href="offer.url" target="_blank" rel="noopener noreferrer" class="offer__name">
          {{ offer.name }}
        </a>
        <span v-else class="offer__name">{{ offer.name }}</span>
        <span class="a-muted">{{ [offer.category_name, offer.vendor].filter(Boolean).join(' · ') }}</span>
        <NuxtLink v-if="offer.product_id" :to="`/manager/products/${offer.product_id}`" class="offer__product">
          → {{ offer.product_name }}
        </NuxtLink>
      </div>
      <div class="offer__numbers">
        <span class="offer__price">{{ formatPrice(offer.price) }}</span>
        <span class="a-badge" :class="inStock ? 'a-badge--success' : 'a-badge--danger'">
          {{ inStock ? `${formatQuantity(offer.quantity)} шт` : 'Нет' }}
        </span>
      </div>
      <div class="offer__actions">
        <template v-if="offer.product_id">
          <button class="a-btn a-btn--ghost a-btn--small" type="button" :disabled="isBusy" @click="emit('unlink')">
            Отвязать
          </button>
        </template>
        <template v-else-if="mode === 'idle'">
          <button class="a-btn a-btn--small" type="button" :disabled="isBusy" @click="mode = 'create'">
            Создать товар
          </button>
          <button class="a-btn a-btn--ghost a-btn--small" type="button" :disabled="isBusy" @click="mode = 'link'">
            Привязать
          </button>
        </template>
      </div>
    </div>

    <form v-if="mode === 'create' && !offer.product_id" class="offer__panel" @submit.prevent="create">
      <select v-model="categoryId" class="a-select" required aria-label="Категория нового товара">
        <option value="" disabled>В какую категорию?</option>
        <option v-for="option in categoryOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
      </select>
      <button class="a-btn" type="submit" :disabled="isBusy || categoryId === ''">Создать черновик</button>
      <button class="a-btn a-btn--ghost" type="button" @click="mode = 'idle'">Отмена</button>
    </form>
    <ProductPicker
      v-if="mode === 'link' && !offer.product_id"
      :initial-search="pickerSearch"
      @select="link"
      @cancel="mode = 'idle'"
    />
  </article>
</template>

<style scoped lang="scss">
.offer {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 16px;

  &__main {
    display: grid;
    grid-template-columns: 56px minmax(0, 1fr);
    gap: 8px 12px;
  }

  &__thumb {
    grid-row: span 2;
    width: 56px;
    height: 56px;
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
    gap: 2px;
    min-width: 0;
  }

  &__name {
    font-weight: 600;
  }

  a.offer__name:hover,
  &__product:hover {
    text-decoration: underline;
  }

  &__product {
    font-size: 14px;
    font-weight: 500;
  }

  &__numbers {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__price {
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    grid-column: 1 / -1;
  }

  &__panel {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
  }
}

/* Десктоп: одна строка, цена и действия справа */
@media (min-width: 1024px) {
  .offer {
    &__main {
      grid-template-columns: 56px minmax(0, 1fr) 160px 240px;
      align-items: center;
    }

    &__thumb {
      grid-row: auto;
    }

    &__numbers {
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
    }

    &__actions {
      grid-column: auto;
      justify-content: flex-end;
    }

    &__panel {
      grid-template-columns: minmax(0, 1fr) auto auto;
      margin-left: 68px;
    }
  }

  :deep(.picker) {
    margin-left: 68px;
  }
}
</style>
