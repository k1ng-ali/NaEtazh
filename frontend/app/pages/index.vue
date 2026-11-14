<script setup lang="ts">
import { computed } from 'vue'
import CatalogSearch from '~/features/catalog/components/CatalogSearch.vue'
import { useCatalogApi } from '~/features/catalog/api'
import { useServicesApi } from '~/features/services/api'

const api = useCatalogApi()
const { data: allCategories, error } = await useAsyncData('home-categories', () => api.listCategories())
// На главной только разделы, подразделы — на странице раздела
const categories = computed(() => allCategories.value?.filter((category) => category.parent_id === null) ?? [])

// Услуги не должны ломать главную: при ошибке блок просто не показываем
const servicesApi = useServicesApi()
const { data: services } = await useAsyncData('home-services', () => servicesApi.listServices())
</script>

<template>
  <div class="container home">
    <CatalogSearch class="home__search" />

    <section class="home__section">
      <h1 class="home__title">Что вам нужно?</h1>

      <p v-if="error" class="home__message" role="alert">
        Не удалось загрузить каталог. Обновите страницу.
      </p>
      <p v-else-if="!categories.length" class="home__message">Каталог скоро появится.</p>
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

    <section v-if="services?.length" class="home__section">
      <div class="home__head">
        <h2 class="home__title">Услуги</h2>
        <NuxtLink to="/services" class="home__all">Все услуги →</NuxtLink>
      </div>
      <nav class="home__grid" aria-label="Услуги">
        <NuxtLink
          v-for="service in services"
          :key="service.slug"
          class="home__tile home__tile--service"
          :to="`/services/${service.slug}`"
        >
          <span>{{ service.name }}</span>
          <span v-if="service.summary" class="home__summary">{{ service.summary }}</span>
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

  &__head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
  }

  &__all {
    font-weight: 600;
    white-space: nowrap;
  }

  &__summary {
    font-size: 13px;
    font-weight: 400;
    opacity: 0.75;
  }

  &__tile {
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    gap: 4px;
    min-height: 92px;
    padding: 14px;
    background: var(--color-surface);
    border-radius: var(--radius-card);
    font-weight: 600;

    // Услуги тёмные, чтобы не путать с разделами каталога
    &--service {
      background: var(--color-text);
      color: var(--color-inverse);
    }
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
