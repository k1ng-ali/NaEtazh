<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import ProductPicker from '~/features/staff/catalog/components/ProductPicker.vue'
import type { ProductRow } from '~/features/staff/catalog/types'
import { formatPrice, formatQuantity } from '~/shared/lib/format'
import type { OrderLinePayload } from '../types'

// Добавление товара в заказ: поиск, количество и цена. Сохраняет страница заказа
defineProps<{
  isSaving: boolean
}>()

const emit = defineEmits<{
  (e: 'save', payload: OrderLinePayload): void
  (e: 'cancel'): void
}>()

const product = ref<ProductRow | null>(null)
const form = reactive({ quantity: '1', unit_price: '' })

const toNumber = (value: string) => Number(value.replace(',', '.'))
// Свой склад плюс партнёр: больше этого добавить не получится
const available = computed(() =>
  product.value ? Number(product.value.stock_quantity) + Number(product.value.offer_quantity ?? 0) : 0,
)
const total = computed(() => {
  const quantity = toNumber(form.quantity)
  const price = toNumber(form.unit_price)
  return quantity > 0 && price > 0 ? quantity * price : null
})
const isPriceChanged = computed(() => product.value !== null && toNumber(form.unit_price) !== Number(product.value.price))

function pick(row: ProductRow) {
  product.value = row
  form.quantity = '1'
  form.unit_price = String(Number(row.price))
}

function submit() {
  if (!product.value) return
  emit('save', {
    product_id: product.value.id,
    quantity: form.quantity.replace(',', '.'),
    unit_price: isPriceChanged.value ? form.unit_price.replace(',', '.') : null,
  })
}
</script>

<template>
  <div class="add-line">
    <ProductPicker v-if="!product" @select="pick" @cancel="emit('cancel')" />

    <form v-else class="add-line__form" @submit.prevent="submit">
      <div class="add-line__product">
        <span>{{ product.name }}</span>
        <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="product = null">Другой</button>
      </div>
      <p class="a-muted">
        Доступно {{ formatQuantity(available) }} {{ product.unit }}:
        на складе {{ formatQuantity(product.stock_quantity) }}, у партнёра {{ formatQuantity(product.offer_quantity ?? 0) }}
      </p>

      <div class="a-grid a-grid--2">
        <label class="a-field">
          <span class="a-field__label">Количество, {{ product.unit }}</span>
          <input v-model="form.quantity" class="a-input" inputmode="decimal" required pattern="\d+([.,]\d{1,3})?">
        </label>
        <label class="a-field">
          <span class="a-field__label">Цена за {{ product.unit }}, ₽</span>
          <input v-model="form.unit_price" class="a-input" inputmode="decimal" required pattern="\d+([.,]\d{1,2})?">
        </label>
      </div>

      <p v-if="toNumber(form.quantity) > available" class="a-error">Столько нет ни на складе, ни у партнёра</p>
      <p v-else-if="total !== null" class="a-muted">
        Строка на {{ formatPrice(total) }}<template v-if="isPriceChanged">, цена на витрине {{ formatPrice(product.price) }}</template>
      </p>
      <p class="a-field__hint">Доставка и подъём не пересчитываются, их обсудите с покупателем.</p>

      <div class="add-line__actions">
        <button class="a-btn" type="submit" :disabled="isSaving || toNumber(form.quantity) > available">
          {{ isSaving ? 'Добавляем…' : 'Добавить в заказ' }}
        </button>
        <button class="a-btn a-btn--ghost" type="button" @click="emit('cancel')">Отмена</button>
      </div>
    </form>
  </div>
</template>

<style scoped lang="scss">
// Форма стоит в начале состава, под заголовком, и отделена от строк заказа снизу
.add-line {
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-line);

  &__form {
    display: flex;
    flex-direction: column;
    gap: 10px;

    p {
      margin: 0;
    }
  }

  &__product {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    font-weight: 600;
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
