<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useCartStore } from '~/features/cart/store'
import { useAddToCart } from '~/features/cart/useAddToCart'
import CatalogSearch from '~/features/catalog/components/CatalogSearch.vue'
import ProductCard from '~/features/catalog/components/ProductCard.vue'
import { useCatalogApi } from '~/features/catalog/api'
import type { Product } from '~/features/catalog/types'

const PAGE_SIZE = 48

const route = useRoute()
const api = useCatalogApi()
const cart = useCartStore()
const addToCart = useAddToCart()

const queryValue = (value: unknown) => (typeof value === 'string' && value ? value : undefined)
const category = computed(() => queryValue(route.query.category))
const search = computed(() => queryValue(route.query.search))

const { data: categories } = await useAsyncData('catalog-categories', () => api.listCategories())
const current = computed(() => categories.value?.find((item) => item.slug === category.value) ?? null)
// В разделе показываем его подразделы, в подразделе — соседние
const section = computed(() => {
  if (!current.value) return null
  const parentId = current.value.parent_id
  return parentId === null ? current.value : (categories.value?.find((item) => item.id === parentId) ?? null)
})
const subcategories = computed(() =>
  section.value ? (categories.value?.filter((item) => item.parent_id === section.value?.id) ?? []) : [],
)
const title = computed(() => (search.value ? `Поиск: ${search.value}` : (current.value?.name ?? 'Каталог')))

const { data, error } = await useAsyncData(
  'catalog-products',
  () => api.listProducts({ category: category.value, search: search.value, limit: PAGE_SIZE }),
  { watch: [category, search] },
)

// Следующие страницы догружаются кнопкой и сбрасываются при смене раздела или поиска
const more = ref<Product[]>([])
const isLoadingMore = ref(false)
const moreError = ref(false)
watch(data, () => {
  more.value = []
  moreError.value = false
})
const items = computed(() => [...(data.value?.items ?? []), ...more.value])
const hasMore = computed(() => items.value.length < (data.value?.total ?? 0))

async function loadMore() {
  isLoadingMore.value = true
  moreError.value = false
  try {
    const page = await api.listProducts({
      category: category.value,
      search: search.value,
      skip: items.value.length,
      limit: PAGE_SIZE,
    })
    more.value.push(...page.items)
  } catch {
    moreError.value = true
  } finally {
    isLoadingMore.value = false
  }
}

// Корзина есть только в браузере: до монтирования показываем как пустую, чтобы не спорить с SSR
const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})

useHead({ title: () => `${current.value?.name ?? 'Каталог'} | Строй База` })
</script>

<template>
  <div class="container catalog">
    <CatalogSearch class="catalog__search" :value="search" />
    <h1 class="catalog__title">{{ title }}</h1>

    <nav v-if="section && subcategories.length && !search" class="catalog__sections" aria-label="Подразделы">
      <NuxtLink
        class="catalog__chip"
        :class="{ 'is-active': current?.id === section.id }"
        :to="{ path: '/catalog', query: { category: section.slug } }"
      >
        Все
      </NuxtLink>
      <NuxtLink
        v-for="item in subcategories"
        :key="item.id"
        class="catalog__chip"
        :class="{ 'is-active': current?.id === item.id }"
        :to="{ path: '/catalog', query: { category: item.slug } }"
      >
        {{ item.name }}
      </NuxtLink>
    </nav>

    <p v-if="error" class="catalog__message" role="alert">
      Не удалось загрузить товары. Обновите страницу.
    </p>
    <p v-else-if="!items.length" class="catalog__message">
      Ничего не нашли. Попробуйте другой запрос.
    </p>
    <template v-else>
      <p class="catalog__count">{{ data?.total }} товаров в наличии</p>
      <div class="catalog__list">
        <ProductCard
          v-for="product in items"
          :key="product.id"
          :product="product"
          :in-cart="isMounted ? cart.quantityOf(product.id) : 0"
          @add="addToCart"
        />
      </div>
      <p v-if="moreError" class="catalog__message" role="alert">Не удалось загрузить. Попробуйте ещё раз.</p>
      <button v-if="hasMore" class="catalog__more" type="button" :disabled="isLoadingMore" @click="loadMore">
        {{ isLoadingMore ? 'Загружаем…' : 'Показать ещё' }}
      </button>
    </template>
  </div>
</template>

<style scoped lang="scss">
.catalog {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__title {
    font-size: 22px;
    font-weight: 700;
  }

  &__sections {
    display: flex;
    gap: 8px;
    // На телефоне подразделы листаются вбок, страница не уезжает
    margin: 0 -16px;
    padding: 0 16px 4px;
    overflow-x: auto;
    scrollbar-width: none;
  }

  &__chip {
    flex: none;
    display: flex;
    align-items: center;
    min-height: 40px;
    padding: 0 14px;
    border-radius: 20px;
    background: var(--color-surface);
    font-size: 14px;
    font-weight: 600;
    white-space: nowrap;

    &.is-active {
      background: var(--color-text);
      color: var(--color-inverse);
    }
  }

  &__message,
  &__count {
    color: var(--color-text-muted);
  }

  &__count {
    font-size: 14px;
  }

  &__list {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
  }

  &__more {
    align-self: center;
    min-height: var(--tap-size);
    padding: 0 24px;
    border: 1.5px solid var(--color-text);
    border-radius: var(--radius-control);
    background: transparent;
    color: var(--color-text);
    font: inherit;
    font-weight: 600;
    cursor: pointer;

    &:disabled {
      opacity: 0.5;
      cursor: default;
    }
  }
}

@media (min-width: 768px) {
  .catalog__list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

/* На десктопе поиск в шапке, а карточек в ряд четыре */
@media (min-width: 1024px) {
  .catalog__search {
    display: none;
  }

  .catalog__title {
    font-size: 28px;
  }

  .catalog__sections {
    flex-wrap: wrap;
    margin: 0;
    padding: 0;
    overflow: visible;
  }

  .catalog__list {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
  }
}
</style>
