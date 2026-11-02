<script setup lang="ts">
import { computed } from 'vue'
import CatalogSearch from '~/features/catalog/components/CatalogSearch.vue'
import ProductCard from '~/features/catalog/components/ProductCard.vue'
import { useCatalogApi } from '~/features/catalog/api'

const route = useRoute()
const api = useCatalogApi()

const queryValue = (value: unknown) => (typeof value === 'string' && value ? value : undefined)
const category = computed(() => queryValue(route.query.category))
const search = computed(() => queryValue(route.query.search))

const { data, error } = await useAsyncData(
  'catalog-products',
  () => api.listProducts({ category: category.value, search: search.value }),
  { watch: [category, search] },
)

useHead({ title: 'Каталог | СтройБаза97' })
</script>

<template>
  <div class="container catalog">
    <CatalogSearch :value="search" />
    <h1 class="catalog__title">Каталог</h1>

    <p v-if="error" class="catalog__message" role="alert">
      Не удалось загрузить товары. Обновите страницу.
    </p>
    <p v-else-if="!data?.items.length" class="catalog__message">
      Ничего не нашли. Попробуйте другой запрос.
    </p>
    <div v-else class="catalog__list">
      <ProductCard v-for="product in data.items" :key="product.id" :product="product" />
    </div>
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

  &__message {
    color: var(--color-text-muted);
  }

  &__list {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
  }
}

@media (min-width: 768px) {
  .catalog__list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .catalog__list {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
