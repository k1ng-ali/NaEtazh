<script setup lang="ts">
import { PRICE_ON_CALL, telHref, useServicesApi } from '~/features/services/api'

const api = useServicesApi()
const [{ data: services, error }, { data: contacts }] = await Promise.all([
  useAsyncData('services', () => api.listServices()),
  useAsyncData('shop-contacts', () => api.getContacts()),
])

useHead({ title: 'Услуги | Строй База' })
</script>

<template>
  <div class="container services">
    <h1 class="services__title">Услуги</h1>
    <p class="muted">Оставьте заявку — менеджер перезвонит, уточнит объём и назовёт цену.</p>

    <p v-if="error" class="muted" role="alert">Не удалось загрузить услуги. Обновите страницу.</p>
    <p v-else-if="!services?.length" class="muted">Список услуг скоро появится.</p>
    <div v-else class="services__list">
      <NuxtLink v-for="service in services" :key="service.slug" :to="`/services/${service.slug}`" class="card services__item">
        <h2 class="services__name">{{ service.name }}</h2>
        <p v-if="service.summary" class="muted">{{ service.summary }}</p>
        <div class="services__bottom">
          <span class="services__price">{{ service.price_text ?? PRICE_ON_CALL }}</span>
          <span class="services__more">Заказать →</span>
        </div>
      </NuxtLink>
    </div>

    <a v-if="contacts?.phone" :href="telHref(contacts.phone)" class="btn btn--ghost services__call">
      Позвонить: {{ contacts.phone }}
    </a>
  </div>
</template>

<style scoped lang="scss">
.services {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__title {
    font-size: 22px;
    font-weight: 700;
  }

  &__list {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
  }

  &__item {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__name {
    font-size: 18px;
    font-weight: 700;
  }

  &__bottom {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    margin-top: auto;
    padding-top: 4px;
  }

  &__price {
    font-weight: 600;
  }

  &__more {
    font-weight: 600;
    white-space: nowrap;
  }

  &__call {
    align-self: flex-start;
  }
}

@media (min-width: 768px) {
  .services__list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .services__title {
    font-size: 28px;
  }

  .services__item:hover {
    outline: 1.5px solid var(--color-text);
  }
}
</style>
