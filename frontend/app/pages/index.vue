<script setup lang="ts">
import CatalogSearch from '~/features/catalog/components/CatalogSearch.vue'
import { useCatalogApi } from '~/features/catalog/api'

const api = useCatalogApi()
const { data: categories, error } = await useAsyncData('home-categories', () => api.listCategories())
</script>

<template>
  <div class="container home">
    <CatalogSearch class="home__search" />

    <section class="home__section">
      <h1 class="home__title">Что вам нужно?</h1>

      <p v-if="error" class="home__message" role="alert">
        Не удалось загрузить каталог. Обновите страницу.
      </p>
      <p v-else-if="!categories?.length" class="home__message">Каталог скоро появится.</p>
      <nav v-else class="home__grid" aria-label="Категории">
        <NuxtLink
          v-for="category in categories"
          :key="category.id"
          class="home__tile"
          :to="{ path: '/catalog', query: { category: category.slug } }"
        >
          {{ category.name }}
        </NuxtLink>
      </nav>
    </section>
  </div>
</template>

<style scoped lang="scss">
.home {
  display: flex;
  flex-direction: column;
  gap: 24px;

  &__section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__title {
    font-size: 22px;
    font-weight: 700;
  }

  &__message {
    color: var(--color-text-muted);
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  &__tile {
    display: flex;
    align-items: flex-end;
    min-height: 92px;
    padding: 14px;
    background: var(--color-surface);
    border-radius: var(--radius-card);
    font-weight: 600;
  }
}

@media (min-width: 768px) {
  .home__grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

/* На десктопе поиск в шапке */
@media (min-width: 1024px) {
  .home__search {
    display: none;
  }

  .home__title {
    font-size: 28px;
  }

  .home__tile {
    min-height: 140px;
    padding: 20px;
    font-size: 18px;

    &:hover {
      outline: 1.5px solid var(--color-text);
    }
  }
}
</style>
