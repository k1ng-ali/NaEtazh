<script setup lang="ts">
// Переключатель между наценкой по категориям и точными ценами товаров
const TABS = [
  { to: '/admin/pricing', label: 'Наценка' },
  { to: '/admin/pricing/products', label: 'Цены товаров' },
]
</script>

<template>
  <nav class="tabs" aria-label="Разделы цен">
    <NuxtLink v-for="tab in TABS" :key="tab.to" :to="tab.to" class="tabs__item" exact-active-class="tabs__item--active">
      {{ tab.label }}
    </NuxtLink>
  </nav>
</template>

<style scoped lang="scss">
.tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  border-radius: var(--radius-control);
  background: var(--color-line);
  align-self: flex-start;

  &__item {
    padding: 8px 14px;
    border-radius: var(--radius-control);
    color: var(--color-text);
    font-weight: 600;
    text-decoration: none;

    &--active {
      background: var(--color-surface);
    }
  }
}
</style>
