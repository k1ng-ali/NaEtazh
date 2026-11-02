<script setup lang="ts">
import { ORDER_STATUS } from '~/features/checkout/labels'
import { formatDateTime } from '~/shared/lib/format'
import type { OrderEvent } from '../types'

defineProps<{
  events: OrderEvent[]
}>()

function title(event: OrderEvent) {
  if (event.action === 'created') return 'Заказ оформлен'
  if (event.action === 'delivery') return 'Доставка'
  if (event.action === 'problem') return 'Проблема'
  return event.status ? ORDER_STATUS[event.status] : 'Статус'
}
</script>

<template>
  <section class="a-card">
    <h2 class="a-subtitle">История</h2>
    <ol class="history">
      <li v-for="(event, index) in events" :key="index" class="history__item" :class="{ 'is-problem': event.action === 'problem' }">
        <div class="history__head">
          <strong>{{ title(event) }}</strong>
          <span class="a-muted">{{ formatDateTime(event.created_at) }}</span>
        </div>
        <span v-if="event.comment">{{ event.comment }}</span>
        <span class="a-muted">{{ event.user_name ?? 'Покупатель' }}</span>
      </li>
    </ol>
  </section>
</template>

<style scoped lang="scss">
.history {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;

  &__item {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding-left: 12px;
    border-left: 2px solid var(--color-line);
    font-size: 14px;

    &.is-problem {
      border-left-color: var(--color-danger);
    }
  }

  &__head {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 4px 12px;
  }
}
</style>
