<script setup lang="ts">
import { computed } from 'vue'
import { useCheckoutApi } from '~/features/checkout/api'
import { DELIVERY_SLOT, LIFTING, ORDER_STATUS } from '~/features/checkout/labels'
import type { OrderStatus } from '~/features/checkout/types'
import { formatPrice, formatQuantity } from '~/shared/lib/format'

const route = useRoute()
const api = useCheckoutApi()
const token = computed(() => String(route.params.token))
const isNew = computed(() => route.query.new === '1')

const { data: order, error, refresh, status } = await useAsyncData(`order-${token.value}`, () => api.getOrder(token.value))
if (error.value) {
  throw createError({ statusCode: 404, statusMessage: 'Заказ не найден', fatal: true })
}

// Путь заказа для шкалы, отмена показывается отдельно
const STEPS: OrderStatus[] = ['new', 'checking', 'confirmed', 'in_delivery', 'delivered']
const currentStep = computed(() => (order.value ? STEPS.indexOf(order.value.status) : -1))
const dateFormat = new Intl.DateTimeFormat('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })
const deliveryDate = computed(() =>
  order.value?.delivery_date ? dateFormat.format(new Date(`${order.value.delivery_date}T00:00:00`)) : 'Как можно скорее',
)

useHead(() => ({
  title: order.value ? `Заказ № ${order.value.number} | Строй База` : 'Заказ | Строй База',
  // Страница по личной ссылке, поисковикам её не показываем
  meta: [{ name: 'robots', content: 'noindex' }],
}))
</script>

<template>
  <div v-if="order" class="container order">
    <section v-if="isNew" class="card order__success" role="status">
      <h1 class="order__title">Заказ № {{ order.number }} принят</h1>
      <p>Менеджер позвонит, проверит наличие и подтвердит время доставки.</p>
      <p class="muted">Эта страница всегда показывает статус заказа. Сохраните ссылку или добавьте в закладки.</p>
    </section>
    <h1 v-else class="order__title">Заказ № {{ order.number }}</h1>

    <div class="order__layout">
      <section class="card order__status">
        <div class="order__status-head">
          <h2 class="order__subtitle">{{ ORDER_STATUS[order.status] }}</h2>
          <button class="btn btn--ghost" type="button" :disabled="status === 'pending'" @click="refresh()">Обновить</button>
        </div>
        <p v-if="order.status === 'canceled'" class="error-text">Заказ отменён. Если это ошибка, позвоните нам.</p>
        <ol v-else class="steps">
          <li
            v-for="(step, index) in STEPS"
            :key="step"
            class="steps__item"
            :class="{ 'is-done': index < currentStep, 'is-current': index === currentStep }"
          >
            {{ ORDER_STATUS[step] }}
          </li>
        </ol>
      </section>

      <section class="card order__details">
        <h2 class="order__subtitle">Доставка</h2>
        <dl class="order__info">
          <dt>Адрес</dt>
          <dd>{{ order.address }}</dd>
          <dt>Когда</dt>
          <dd>{{ deliveryDate }}<template v-if="order.delivery_slot">, {{ DELIVERY_SLOT[order.delivery_slot].toLowerCase() }}</template></dd>
          <dt>Подъём</dt>
          <dd>{{ LIFTING[order.lifting_type] }}</dd>
          <dt>Оплата</dt>
          <dd>Наличными при получении</dd>
        </dl>
      </section>

      <section class="card order__lines">
        <h2 class="order__subtitle">Состав</h2>
        <div v-for="(line, index) in order.lines" :key="index" class="order__line">
          <span>{{ line.name }}</span>
          <span class="muted">{{ formatQuantity(line.quantity) }} {{ line.unit }} × {{ formatPrice(line.unit_price) }}</span>
          <strong>{{ formatPrice(line.total) }}</strong>
        </div>
        <div v-for="service in order.services" :key="service.type" class="order__line">
          <span>{{ service.name }}</span>
          <span />
          <strong>{{ Number(service.price) ? formatPrice(service.price) : 'Бесплатно' }}</strong>
        </div>
        <div class="order__line order__total">
          <span>Итого</span>
          <span />
          <strong>{{ formatPrice(order.total) }}</strong>
        </div>
      </section>
    </div>

    <NuxtLink to="/catalog" class="btn btn--ghost order__more">Вернуться в каталог</NuxtLink>
  </div>
</template>

<style scoped lang="scss">
.order {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__success {
    display: flex;
    flex-direction: column;
    gap: 8px;
    border: 1.5px solid var(--color-success);
  }

  &__title {
    font-size: 22px;
    font-weight: 700;
  }

  &__layout {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  &__subtitle {
    font-size: 18px;
    font-weight: 700;
  }

  &__status,
  &__details,
  &__lines {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__status-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  &__info {
    display: grid;
    grid-template-columns: 90px minmax(0, 1fr);
    gap: 8px 12px;
    margin: 0;

    dt {
      color: var(--color-text-muted);
    }

    dd {
      margin: 0;
    }
  }

  &__line {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 2px 12px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--color-line);

    strong {
      grid-column: 2;
      grid-row: 1 / span 2;
      align-self: center;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }
  }

  &__total {
    border-bottom: 0;
    font-size: 18px;
    font-weight: 700;
  }

  &__more {
    align-self: flex-start;
  }
}

.steps {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin: 0;
  padding: 0;
  list-style: none;

  &__item {
    position: relative;
    padding: 0 0 16px 28px;
    color: var(--color-text-muted);

    // Точка и линия к следующему шагу
    &::before {
      position: absolute;
      top: 4px;
      left: 0;
      width: 14px;
      height: 14px;
      border: 2px solid var(--color-line);
      border-radius: 50%;
      background: var(--color-surface);
      content: '';
    }

    &:not(:last-child)::after {
      position: absolute;
      top: 20px;
      bottom: 0;
      left: 8px;
      width: 2px;
      background: var(--color-line);
      content: '';
    }

    &.is-done,
    &.is-current {
      color: var(--color-text);

      &::before {
        border-color: var(--color-text);
        background: var(--color-text);
      }
    }

    &.is-done::after {
      background: var(--color-text);
    }

    &.is-current {
      font-weight: 700;
    }
  }
}

@media (min-width: 1024px) {
  .order {
    &__title {
      font-size: 28px;
    }

    &__layout {
      display: grid;
      grid-template-columns: 340px minmax(0, 1fr);
      align-items: start;
      gap: 24px;
    }

    &__lines {
      grid-column: 2;
      grid-row: 1 / span 2;
    }
  }
}
</style>
