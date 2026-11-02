<script setup lang="ts">
import { reactive, watch } from 'vue'
import { formatQuantity } from '~/shared/lib/format'
import type { Stock, StockPayload, Warehouse } from '../types'

const props = defineProps<{
  stock: Stock[]
  warehouses: Warehouse[]
  unit: string
  isSaving: boolean
}>()

const emit = defineEmits<{
  (e: 'save', payload: StockPayload): void
}>()

// Черновик значений по каждому складу
const drafts = reactive<Record<number, { quantity: string; unit_cost: string }>>({})

watch(
  () => [props.stock, props.warehouses] as const,
  ([stock, warehouses]) => {
    for (const warehouse of warehouses) {
      const item = stock.find((row) => row.warehouse_id === warehouse.id)
      drafts[warehouse.id] = {
        quantity: item ? String(Number(item.quantity)) : '0',
        unit_cost: item?.unit_cost ?? '',
      }
    }
  },
  { immediate: true },
)

const reserved = (warehouseId: number) =>
  Number(props.stock.find((row) => row.warehouse_id === warehouseId)?.reserved ?? 0)

function save(warehouseId: number) {
  const draft = drafts[warehouseId]
  if (!draft) return
  emit('save', {
    warehouse_id: warehouseId,
    quantity: draft.quantity.replace(',', '.') || '0',
    unit_cost: draft.unit_cost.trim() ? draft.unit_cost.replace(',', '.') : null,
  })
}
</script>

<template>
  <section class="a-card">
    <h2 class="a-subtitle">Свой склад</h2>
    <div v-for="warehouse in warehouses" :key="warehouse.id" class="stock">
      <p class="stock__name">{{ warehouse.name }}</p>
      <div v-if="drafts[warehouse.id]" class="stock__row">
        <label class="a-field">
          <span class="a-field__label">Остаток, {{ unit }}</span>
          <input v-model="drafts[warehouse.id]!.quantity" class="a-input" inputmode="decimal" pattern="\d+([.,]\d{1,3})?">
        </label>
        <label class="a-field">
          <span class="a-field__label">Себестоимость, ₽</span>
          <input v-model="drafts[warehouse.id]!.unit_cost" class="a-input" inputmode="decimal" pattern="\d+([.,]\d{1,2})?">
        </label>
        <button class="a-btn a-btn--ghost" type="button" :disabled="isSaving" @click="save(warehouse.id)">
          Сохранить
        </button>
      </div>
      <p v-if="reserved(warehouse.id) > 0" class="a-field__hint">
        В резерве под заказы: {{ formatQuantity(reserved(warehouse.id)) }} {{ unit }}
      </p>
    </div>
  </section>
</template>

<style scoped lang="scss">
.stock {
  display: flex;
  flex-direction: column;
  gap: 8px;

  &__name {
    font-weight: 600;
  }

  &__row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
    align-items: end;

    .a-btn {
      grid-column: 1 / -1;
    }
  }
}
</style>
