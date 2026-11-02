<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { formatPrice } from '~/shared/lib/format'
import { useAdminCatalogApi } from '../api'
import type { ProductRow } from '../types'

// Самостоятельный виджет поиска товара: сам ходит в API, наружу отдаёт выбор
const props = defineProps<{
  initialSearch?: string
}>()

const emit = defineEmits<{
  (e: 'select', product: ProductRow): void
  (e: 'cancel'): void
}>()

const api = useAdminCatalogApi()
const search = ref(props.initialSearch ?? '')
const items = ref<ProductRow[]>([])
const isLoading = ref(false)

let timer: ReturnType<typeof setTimeout> | undefined
watch(
  search,
  (value) => {
    clearTimeout(timer)
    timer = setTimeout(async () => {
      isLoading.value = true
      try {
        items.value = (await api.listProducts({ search: value.trim() || undefined, limit: 8 })).items
      } finally {
        isLoading.value = false
      }
    }, 250)
  },
  { immediate: true },
)
onBeforeUnmount(() => clearTimeout(timer))
</script>

<template>
  <div class="picker">
    <div class="picker__head">
      <input v-model="search" class="a-input" type="search" placeholder="Найти товар витрины" aria-label="Поиск товара">
      <button class="a-btn a-btn--ghost" type="button" @click="emit('cancel')">Отмена</button>
    </div>
    <p v-if="!isLoading && !items.length" class="a-muted">Ничего не нашли</p>
    <ul class="picker__list">
      <li v-for="item in items" :key="item.id">
        <button class="picker__item" type="button" @click="emit('select', item)">
          <span>{{ item.name }}</span>
          <span class="a-muted">{{ formatPrice(item.price) }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped lang="scss">
.picker {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-radius: var(--radius-control);
  background: var(--color-bg);

  &__head {
    display: flex;
    gap: 8px;
  }

  &__list {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  &__item {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    width: 100%;
    min-height: var(--tap-size);
    padding: 8px 10px;
    border: 0;
    border-radius: 8px;
    background: transparent;
    color: var(--color-text);
    font: inherit;
    text-align: left;
    cursor: pointer;

    &:hover {
      background: var(--color-surface);
    }
  }
}
</style>
