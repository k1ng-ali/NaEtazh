<script setup lang="ts">
import { reactive, watch } from 'vue'
import { DELIVERY_SLOT } from '~/features/checkout/labels'
import type { DeliverySlot } from '~/features/checkout/types'
import type { Courier, DeliveryPayload, OrderAdmin } from '../types'

const props = defineProps<{
  order: OrderAdmin
  couriers: Courier[]
  isSaving: boolean
}>()

const emit = defineEmits<{
  (e: 'save', payload: DeliveryPayload): void
}>()

const form = reactive({ courierId: '' as number | '', date: '', slot: '' as DeliverySlot | '' })

// Пожелание покупателя подставляем как черновик, пока менеджер не согласовал своё
watch(
  () => props.order,
  (order) => {
    Object.assign(form, {
      courierId: order.courier_id ?? '',
      date: order.planned_date ?? order.delivery_date ?? '',
      slot: order.planned_slot ?? order.delivery_slot ?? '',
    })
  },
  { immediate: true },
)

function submit() {
  emit('save', {
    courier_id: form.courierId === '' ? null : form.courierId,
    planned_date: form.date || null,
    planned_slot: form.slot || null,
  })
}
</script>

<template>
  <form class="a-card delivery" @submit.prevent="submit">
    <h2 class="a-subtitle">Доставка</h2>
    <p class="a-muted">
      Покупатель просил:
      {{ order.delivery_date ?? 'как можно скорее' }}{{ order.delivery_slot ? `, ${DELIVERY_SLOT[order.delivery_slot].toLowerCase()}` : '' }}
    </p>
    <div class="delivery__grid">
      <label class="a-field">
        <span class="a-field__label">Курьер</span>
        <select v-model="form.courierId" class="a-select">
          <option value="">Не назначен</option>
          <option v-for="courier in couriers" :key="courier.id" :value="courier.id">{{ courier.name }}</option>
        </select>
      </label>
      <label class="a-field">
        <span class="a-field__label">Дата</span>
        <input v-model="form.date" class="a-input" type="date">
      </label>
      <label class="a-field">
        <span class="a-field__label">Время</span>
        <select v-model="form.slot" class="a-select">
          <option value="">Любое</option>
          <option v-for="(label, value) in DELIVERY_SLOT" :key="value" :value="value">{{ label }}</option>
        </select>
      </label>
    </div>
    <p v-if="!couriers.length" class="a-field__hint">Курьеров нет. Владелец добавляет их в разделе «Сотрудники».</p>
    <button class="a-btn a-btn--ghost delivery__save" type="submit" :disabled="isSaving">Сохранить доставку</button>
  </form>
</template>

<style scoped lang="scss">
.delivery {
  &__grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
  }

  &__save {
    align-self: flex-start;
  }
}

@media (min-width: 640px) {
  .delivery__grid {
    grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr) minmax(0, 1fr);
  }
}
</style>
