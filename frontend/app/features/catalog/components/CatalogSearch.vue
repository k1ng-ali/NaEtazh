<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  value?: string
}>()

const query = ref(props.value ?? '')

watch(
  () => props.value,
  (value) => {
    query.value = value ?? ''
  },
)

async function submit() {
  const search = query.value.trim()
  await navigateTo({ path: '/catalog', query: search ? { search } : {} })
}
</script>

<template>
  <form class="search" role="search" @submit.prevent="submit">
    <input
      v-model="query"
      class="search__input"
      type="search"
      aria-label="Поиск товаров"
      placeholder="Например, Ротбанд"
    >
    <button class="search__button" type="submit">Найти</button>
  </form>
</template>

<style scoped lang="scss">
.search {
  display: flex;
  gap: 8px;
  padding: 4px;
  background: var(--color-surface);
  border: 1.5px solid var(--color-text);
  border-radius: var(--radius-card);

  &__input {
    flex: 1;
    min-width: 0;
    height: var(--tap-size);
    padding-inline: 10px;
    border: 0;
    outline: 0;
    background: transparent;
    color: var(--color-text);
  }

  &__button {
    height: var(--tap-size);
    padding-inline: 16px;
    border: 0;
    border-radius: var(--radius-control);
    background: var(--color-text);
    color: var(--color-inverse);
    font-weight: 600;
    cursor: pointer;
  }
}
</style>
