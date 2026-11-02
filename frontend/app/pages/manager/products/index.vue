<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useAdminCatalogApi } from '~/features/staff/catalog/api'
import ProductTable from '~/features/staff/catalog/components/ProductTable.vue'
import { useAdminCatalogStore } from '~/features/staff/catalog/store'
import type { ProductFilters, ProductRowList, ProductStatus } from '~/features/staff/catalog/types'
import { errorMessage } from '~/features/staff/shared/errors'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin', 'manager'] })
useHead({ title: 'Товары | Кабинет' })

const PAGE_SIZE = 50
const STATUSES: { value: ProductStatus | ''; label: string }[] = [
  { value: '', label: 'Все статусы' },
  { value: 'published', label: 'На витрине' },
  { value: 'draft', label: 'Черновики' },
  { value: 'archived', label: 'В архиве' },
]

const api = useAdminCatalogApi()
const catalog = useAdminCatalogStore()
const route = useRoute()
const router = useRouter()

// Фильтры живут в адресе, чтобы после карточки товара вернуться к тому же списку
const text = (value: unknown) => (typeof value === 'string' ? value : '')
const filters = computed<ProductFilters>(() => ({
  search: text(route.query.search) || undefined,
  category_id: Number(route.query.category) || undefined,
  status: (text(route.query.status) as ProductStatus) || undefined,
  skip: Number(route.query.skip) || 0,
  limit: PAGE_SIZE,
}))

const search = ref(filters.value.search ?? '')
const data = ref<ProductRowList | null>(null)
const isLoading = ref(false)
const errorText = ref('')

const page = computed(() => Math.floor((filters.value.skip ?? 0) / PAGE_SIZE) + 1)
const pages = computed(() => Math.max(1, Math.ceil((data.value?.total ?? 0) / PAGE_SIZE)))

function setQuery(values: Record<string, string | number | undefined>) {
  const query = { ...route.query, ...values }
  for (const key of Object.keys(query)) {
    if (query[key] === undefined || query[key] === '' || query[key] === 0) delete query[key]
  }
  router.replace({ query })
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, (value) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => setQuery({ search: value.trim(), skip: undefined }), 300)
})

async function load() {
  isLoading.value = true
  errorText.value = ''
  try {
    data.value = await api.listProducts(filters.value)
  } catch (error) {
    errorText.value = errorMessage(error, 'Не удалось загрузить товары')
  } finally {
    isLoading.value = false
  }
}

watch(filters, load)
onMounted(() => Promise.all([load(), catalog.loadCategories()]))
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <div>
        <h1 class="a-title">Товары</h1>
        <p class="a-muted">{{ data ? `Всего ${data.total}` : 'Загружаем…' }}</p>
      </div>
      <NuxtLink to="/manager/products/new" class="a-btn">Добавить товар</NuxtLink>
    </div>

    <div class="filters">
      <input
        v-model="search"
        class="a-input filters__search"
        type="search"
        placeholder="Название или артикул"
        aria-label="Поиск товаров"
      >
      <select
        class="a-select"
        aria-label="Категория"
        :value="filters.category_id ?? ''"
        @change="setQuery({ category: ($event.target as HTMLSelectElement).value, skip: undefined })"
      >
        <option value="">Все категории</option>
        <option v-for="option in catalog.categoryOptions" :key="option.id" :value="option.id">
          {{ option.label }}
        </option>
      </select>
      <select
        class="a-select"
        aria-label="Статус"
        :value="filters.status ?? ''"
        @change="setQuery({ status: ($event.target as HTMLSelectElement).value, skip: undefined })"
      >
        <option v-for="option in STATUSES" :key="option.value" :value="option.value">{{ option.label }}</option>
      </select>
    </div>

    <p v-if="errorText" class="a-error" role="alert">{{ errorText }}</p>
    <div v-else-if="data && !data.items.length" class="a-card a-empty">
      Товаров не нашли. Добавьте товар вручную или создайте его из выгрузки партнёра.
    </div>
    <ProductTable
      v-else-if="data"
      :items="data.items"
      :category-names="catalog.categoryNames"
      :class="{ 'is-loading': isLoading }"
    />

    <div v-if="pages > 1" class="a-pager">
      <button
        class="a-btn a-btn--ghost"
        type="button"
        :disabled="page <= 1"
        @click="setQuery({ skip: (page - 2) * PAGE_SIZE })"
      >
        Назад
      </button>
      <span class="a-muted">Страница {{ page }} из {{ pages }}</span>
      <button
        class="a-btn a-btn--ghost"
        type="button"
        :disabled="page >= pages"
        @click="setQuery({ skip: page * PAGE_SIZE })"
      >
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

.is-loading {
  opacity: 0.6;
}

@media (min-width: 768px) {
  .filters {
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) minmax(0, 1fr);
  }
}
</style>
