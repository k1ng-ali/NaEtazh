<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { Tariff, TariffPayload } from '../types'

const props = defineProps<{
  complexId: number | null
  tariff: Tariff | null
  canEdit: boolean
  isSaving: boolean
}>()

const emit = defineEmits<{
  (e: 'save', payload: TariffPayload): void
}>()

const FIELDS = [
  { key: 'delivery_price', label: 'Доставка, ₽', hint: 'Цена для покупателя' },
  { key: 'delivery_free_from', label: 'Бесплатно от, ₽', hint: 'Сумма товаров. Пусто — всегда платно' },
  { key: 'delivery_cost', label: 'Наш расход на рейс, ₽', hint: 'Для расчёта прибыли' },
  { key: 'lift_price_per_100kg', label: 'Лифт, ₽ за 100 кг', hint: 'Каждые начатые 100 кг' },
  { key: 'lift_min_price', label: 'Подъём минимум, ₽', hint: 'Даже за один мешок' },
  { key: 'stairs_price_per_100kg_floor', label: 'Лестница, ₽ за 100 кг и этаж', hint: '' },
  { key: 'lifting_cost_percent', label: 'Грузчикам, % от подъёма', hint: 'Для расчёта прибыли' },
] as const

type FieldKey = (typeof FIELDS)[number]['key']
const form = reactive<Record<FieldKey, string>>({
  delivery_price: '',
  delivery_free_from: '',
  delivery_cost: '0',
  lift_price_per_100kg: '',
  lift_min_price: '0',
  stairs_price_per_100kg_floor: '',
  lifting_cost_percent: '0',
})

watch(
  () => props.tariff,
  (tariff) => {
    if (!tariff) return
    for (const field of FIELDS) form[field.key] = tariff[field.key] ? String(Number(tariff[field.key])) : ''
  },
  { immediate: true },
)

const clean = (value: string) => value.trim().replace(',', '.')

function submit() {
  emit('save', {
    complex_id: props.complexId,
    delivery_price: clean(form.delivery_price),
    delivery_free_from: clean(form.delivery_free_from) || null,
    delivery_cost: clean(form.delivery_cost) || '0',
    lift_price_per_100kg: clean(form.lift_price_per_100kg),
    lift_min_price: clean(form.lift_min_price) || '0',
    stairs_price_per_100kg_floor: clean(form.stairs_price_per_100kg_floor),
    lifting_cost_percent: clean(form.lifting_cost_percent) || '0',
  })
}
</script>

<template>
  <form class="tariff" @submit.prevent="submit">
    <div class="tariff__grid">
      <label v-for="field in FIELDS" :key="field.key" class="a-field">
        <span class="a-field__label">{{ field.label }}</span>
        <input
          v-model="form[field.key]"
          class="a-input"
          inputmode="decimal"
          pattern="\d+([.,]\d{1,2})?"
          :required="['delivery_price', 'lift_price_per_100kg', 'stairs_price_per_100kg_floor'].includes(field.key)"
          :disabled="!canEdit"
        >
        <span v-if="field.hint" class="a-field__hint">{{ field.hint }}</span>
      </label>
    </div>
    <button v-if="canEdit" class="a-btn" type="submit" :disabled="isSaving">Сохранить тариф</button>
  </form>
</template>

<style scoped lang="scss">
.tariff {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;

  &__grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    width: 100%;
  }
}

@media (min-width: 1024px) {
  .tariff__grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
