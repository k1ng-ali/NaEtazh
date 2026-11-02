<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import type { AdminProduct, ProductPayload, ProductStatus } from '../types'

const props = defineProps<{
  product: AdminProduct | null
  categoryOptions: { id: number; label: string }[]
  hasOffers: boolean
  isSaving: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: ProductPayload): void
}>()

const UNITS = ['шт', 'мешок', 'лист', 'упак', 'м', 'м²', 'м³', 'кг', 'рулон', 'ведро']
const STATUSES: { value: ProductStatus; label: string }[] = [
  { value: 'draft', label: 'Черновик' },
  { value: 'published', label: 'На витрине' },
  { value: 'archived', label: 'В архиве' },
]

interface AttributeRow {
  key: string
  value: string
}

const emptyForm = () => ({
  name: '',
  category_id: '' as number | '',
  unit: 'шт',
  sku: '',
  price: '',
  is_price_manual: true,
  status: 'draft' as ProductStatus,
  description: '',
  weight_kg: '',
  length_mm: '',
  volume_m3: '',
  attributes: [] as AttributeRow[],
})

const form = reactive(emptyForm())

watch(
  () => props.product,
  (product) => {
    Object.assign(form, emptyForm())
    if (!product) return
    Object.assign(form, {
      name: product.name,
      category_id: product.category_id,
      unit: product.unit,
      sku: product.sku,
      price: product.price,
      is_price_manual: product.is_price_manual,
      status: product.status,
      description: product.description ?? '',
      weight_kg: product.weight_kg ?? '',
      length_mm: product.length_mm?.toString() ?? '',
      volume_m3: product.volume_m3 ?? '',
      attributes: Object.entries(product.attributes).map(([key, value]) => ({ key, value: String(value) })),
    })
  },
  { immediate: true },
)

// Единица продажи из выгрузки может не входить в список
const units = computed(() => (UNITS.includes(form.unit) ? UNITS : [form.unit, ...UNITS]))
const priceLocked = computed(() => !form.is_price_manual)

const orNull = (value: string) => (value.trim() === '' ? null : value.trim().replace(',', '.'))

function submit() {
  const attributes = Object.fromEntries(
    form.attributes.filter((row) => row.key.trim()).map((row) => [row.key.trim(), row.value.trim()]),
  )
  emit('submit', {
    name: form.name.trim(),
    category_id: Number(form.category_id),
    unit: form.unit,
    sku: form.sku.trim() || null,
    price: form.price.toString().replace(',', '.'),
    is_price_manual: form.is_price_manual,
    status: form.status,
    description: form.description.trim() || null,
    weight_kg: orNull(form.weight_kg),
    length_mm: form.length_mm.trim() ? Number(form.length_mm) : null,
    volume_m3: orNull(form.volume_m3),
    attributes,
  })
}
</script>

<template>
  <form id="product-form" class="form" @submit.prevent="submit">
    <section class="a-card">
      <h2 class="a-subtitle">Основное</h2>
      <label class="a-field">
        <span class="a-field__label">Название</span>
        <input v-model="form.name" class="a-input" required maxlength="250" placeholder="Штукатурка гипсовая Кнауф Ротбанд, 30 кг">
      </label>
      <div class="a-grid a-grid--2">
        <label class="a-field">
          <span class="a-field__label">Категория</span>
          <select v-model="form.category_id" class="a-select" required>
            <option value="" disabled>Выберите категорию</option>
            <option v-for="option in categoryOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
          </select>
        </label>
        <label class="a-field">
          <span class="a-field__label">Единица продажи</span>
          <select v-model="form.unit" class="a-select">
            <option v-for="unit in units" :key="unit" :value="unit">{{ unit }}</option>
          </select>
        </label>
      </div>
      <label class="a-field">
        <span class="a-field__label">Артикул</span>
        <input v-model="form.sku" class="a-input" maxlength="64" placeholder="Пусто — создадим сами">
      </label>
      <label class="a-field">
        <span class="a-field__label">Описание</span>
        <textarea v-model="form.description" class="a-textarea" maxlength="10000" />
      </label>
    </section>

    <section class="a-card">
      <h2 class="a-subtitle">Цена и видимость</h2>
      <div class="a-grid a-grid--2">
        <label class="a-field">
          <span class="a-field__label">Цена продажи, ₽</span>
          <input
            v-model="form.price"
            class="a-input"
            inputmode="decimal"
            required
            pattern="\d+([.,]\d{1,2})?"
            :disabled="priceLocked"
          >
          <span v-if="priceLocked" class="a-field__hint">Считается от цены партнёра по правилам наценки</span>
        </label>
        <label class="a-field">
          <span class="a-field__label">Статус</span>
          <select v-model="form.status" class="a-select">
            <option v-for="option in STATUSES" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </label>
      </div>
      <label v-if="hasOffers || !form.is_price_manual" class="a-check">
        <input v-model="form.is_price_manual" type="checkbox">
        Задать цену вручную, а не от цены партнёра
      </label>
    </section>

    <section class="a-card">
      <h2 class="a-subtitle">Для доставки</h2>
      <div class="a-grid a-grid--3">
        <label class="a-field">
          <span class="a-field__label">Вес, кг</span>
          <input v-model="form.weight_kg" class="a-input" inputmode="decimal" pattern="\d+([.,]\d{1,3})?">
        </label>
        <label class="a-field">
          <span class="a-field__label">Длина, мм</span>
          <input v-model="form.length_mm" class="a-input" inputmode="numeric" pattern="\d+">
          <span class="a-field__hint">Для проверки грузового лифта</span>
        </label>
        <label class="a-field">
          <span class="a-field__label">Объём, м³</span>
          <input v-model="form.volume_m3" class="a-input" inputmode="decimal" pattern="\d+([.,]\d{1,4})?">
        </label>
      </div>
    </section>

    <section class="a-card">
      <div class="form__head">
        <h2 class="a-subtitle">Характеристики</h2>
        <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="form.attributes.push({ key: '', value: '' })">
          Добавить
        </button>
      </div>
      <p v-if="!form.attributes.length" class="a-muted">Например, «Расход» — «8,5 кг/м² при слое 10 мм»</p>
      <div v-for="(row, index) in form.attributes" :key="index" class="form__attribute">
        <input v-model="row.key" class="a-input" placeholder="Название" aria-label="Название характеристики" maxlength="60">
        <input v-model="row.value" class="a-input" placeholder="Значение" aria-label="Значение характеристики" maxlength="200">
        <button
          class="a-btn a-btn--danger a-btn--small"
          type="button"
          aria-label="Удалить характеристику"
          @click="form.attributes.splice(index, 1)"
        >
          ✕
        </button>
      </div>
    </section>

    <button class="a-btn form__save" type="submit" :disabled="isSaving">
      {{ isSaving ? 'Сохраняем…' : 'Сохранить' }}
    </button>
  </form>
</template>

<style scoped lang="scss">
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  &__attribute {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr) auto;
    gap: 8px;
  }

  // На телефоне кнопка всегда под рукой над нижним меню
  &__save {
    position: sticky;
    bottom: calc(72px + env(safe-area-inset-bottom));
    z-index: 5;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.16);
  }
}

@media (min-width: 1024px) {
  .form__save {
    position: static;
    align-self: flex-start;
    min-width: 200px;
    box-shadow: none;
  }
}
</style>
