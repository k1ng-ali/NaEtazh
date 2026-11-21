<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import ProductPicker from '~/features/staff/catalog/components/ProductPicker.vue'
import type { ProductRow } from '~/features/staff/catalog/types'
import { usePricingApi } from '~/features/staff/pricing/api'
import { calcFixedPrice } from '~/features/staff/pricing/calc'
import PricingTabs from '~/features/staff/pricing/components/PricingTabs.vue'
import type { ProductPrice } from '~/features/staff/pricing/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'
import { formatPrice } from '~/shared/lib/format'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin'] })
useHead({ title: 'Цены товаров | Кабинет' })

const api = usePricingApi()
const toast = useToast()

const rows = ref<ProductPrice[]>([])
const loadError = ref('')
const isSaving = ref(false)
const isPicking = ref(false)

// Товар в форме: из поиска или из списка, закупка нужна для подсказки
const selected = ref<{ id: number; name: string; cost: number | null } | null>(null)
const form = reactive({ price: '', min_profit: '0' })

const toNumber = (value: string) => Number(value.replace(',', '.'))
const isRaised = (row: ProductPrice) => Number(row.sale_price) > Number(row.price)
const profit = (row: ProductPrice) => (row.cost === null ? null : Number(row.sale_price) - Number(row.cost))

// Что будет на витрине с введёнными числами
const preview = computed(() => {
  const price = toNumber(form.price)
  const minProfit = toNumber(form.min_profit) || 0
  if (!selected.value || !(price > 0)) return null
  const cost = selected.value.cost
  const sale = calcFixedPrice(price, cost, minProfit)
  return {
    cost,
    sale,
    profit: cost === null ? null : sale - cost,
    // Выше этой закупки цена начнёт подниматься вслед за ней
    raiseFrom: price - minProfit,
    isRaised: sale > price,
  }
})

function pickProduct(product: ProductRow) {
  selected.value = {
    id: product.id,
    name: product.name,
    cost: product.offer_price === null ? null : Number(product.offer_price),
  }
  const existing = rows.value.find((row) => row.product_id === product.id)
  form.price = existing ? String(Number(existing.price)) : String(Number(product.price))
  form.min_profit = existing ? String(Number(existing.min_profit)) : '0'
  isPicking.value = false
}

function edit(row: ProductPrice) {
  selected.value = { id: row.product_id, name: row.product_name, cost: row.cost === null ? null : Number(row.cost) }
  form.price = String(Number(row.price))
  form.min_profit = String(Number(row.min_profit))
  isPicking.value = false
}

function reset() {
  selected.value = null
  form.price = ''
  form.min_profit = '0'
}

async function load() {
  try {
    rows.value = await api.listProductPrices()
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить цены')
  }
}

async function submit() {
  if (!selected.value) return
  isSaving.value = true
  try {
    const saved = await api.saveProductPrice({
      product_id: selected.value.id,
      price: form.price.replace(',', '.'),
      min_profit: form.min_profit.replace(',', '.'),
    })
    toast.success(`Сохранено. На витрине ${formatPrice(saved.sale_price)}`)
    reset()
    await load()
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSaving.value = false
  }
}

async function remove(row: ProductPrice) {
  if (!confirm(`Убрать точную цену у «${row.product_name}»? Цену снова посчитает наценка категории.`)) return
  try {
    await api.deleteProductPrice(row.product_id)
    if (selected.value?.id === row.product_id) reset()
    await load()
    toast.success('Точная цена убрана')
  } catch (error) {
    toast.error(errorMessage(error))
  }
}

onMounted(load)
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <div>
        <h1 class="a-title">Цены товаров</h1>
        <p class="a-muted">
          Точная цена продажи вместо наценки. Если закупка у партнёра вырастет и прибыль станет меньше минимума,
          цена поднимется сама, а когда закупка упадёт — вернётся к точной.
        </p>
      </div>
    </div>
    <PricingTabs />

    <p v-if="loadError" class="a-error" role="alert">{{ loadError }}</p>

    <div class="layout">
      <section class="a-card">
        <h2 class="a-subtitle">Товары с точной ценой</h2>
        <p v-if="!rows.length" class="a-muted">Пока нет. Все товары партнёра считаются по наценке.</p>
        <div v-for="row in rows" :key="row.product_id" class="row">
          <div class="row__name">
            <span>{{ row.product_name }}</span>
            <span class="a-muted">{{ row.product_sku }}</span>
          </div>
          <div class="row__prices">
            <span class="row__sale">{{ formatPrice(row.sale_price) }}</span>
            <span class="a-muted">
              точная {{ formatPrice(row.price) }}, прибыль не меньше {{ formatPrice(row.min_profit) }}
            </span>
          </div>
          <div class="row__meta">
            <span v-if="row.cost !== null" class="a-muted">
              Закупка {{ formatPrice(row.cost) }}, прибыль {{ formatPrice(profit(row)!) }}
            </span>
            <span v-else class="a-muted">Нет предложения партнёра</span>
            <span v-if="row.is_price_manual" class="a-badge a-badge--danger">Цена вручную, правило не действует</span>
            <span v-else-if="isRaised(row)" class="a-badge a-badge--warning">Поднята из-за закупки</span>
          </div>
          <div class="row__actions">
            <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="edit(row)">Изменить</button>
            <button class="a-btn a-btn--danger a-btn--small" type="button" @click="remove(row)">Убрать</button>
          </div>
        </div>
      </section>

      <form class="a-card form" @submit.prevent="submit">
        <h2 class="a-subtitle">Задать цену</h2>

        <ProductPicker v-if="isPicking" @select="pickProduct" @cancel="isPicking = false" />
        <div v-else-if="selected" class="form__product">
          <span>{{ selected.name }}</span>
          <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="isPicking = true">Другой</button>
        </div>
        <button v-else class="a-btn a-btn--ghost" type="button" @click="isPicking = true">Выбрать товар</button>

        <template v-if="selected && !isPicking">
          <div class="a-grid a-grid--2">
            <label class="a-field">
              <span class="a-field__label">Цена продажи, ₽</span>
              <input v-model="form.price" class="a-input" inputmode="decimal" required pattern="\d+([.,]\d{1,2})?">
            </label>
            <label class="a-field">
              <span class="a-field__label">Минимум прибыли, ₽</span>
              <input v-model="form.min_profit" class="a-input" inputmode="decimal" required pattern="\d+([.,]\d{1,2})?">
            </label>
          </div>

          <div v-if="preview" class="form__preview">
            <template v-if="preview.cost !== null">
              <p>
                Закупка сейчас {{ formatPrice(preview.cost) }} → на витрине {{ formatPrice(preview.sale) }},
                прибыль {{ formatPrice(preview.profit!) }}
              </p>
              <p v-if="preview.isRaised" class="a-error">
                Цена ниже закупки плюс минимум, поэтому на витрине будет {{ formatPrice(preview.sale) }}
              </p>
              <p v-else class="a-muted">
                Если закупка станет выше {{ formatPrice(preview.raiseFrom) }}, цена начнёт расти вслед за ней
              </p>
            </template>
            <p v-else class="a-muted">
              У товара нет предложения партнёра: цена будет ровно {{ formatPrice(preview.sale) }}, минимум не с чем сравнить
            </p>
          </div>

          <div class="form__actions">
            <button class="a-btn" type="submit" :disabled="isSaving">{{ isSaving ? 'Сохраняем…' : 'Сохранить' }}</button>
            <button class="a-btn a-btn--ghost" type="button" @click="reset">Отмена</button>
          </div>
        </template>
      </form>
    </div>
  </div>
</template>

<style scoped lang="scss">
.layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.row {
  display: flex;
  flex-direction: column;
  gap: 4px;

  & + & {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--color-line);
  }

  &__name {
    display: flex;
    flex-direction: column;
    font-weight: 600;

    .a-muted {
      font-size: 13px;
      font-weight: 400;
    }
  }

  &__prices,
  &__meta {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 4px 10px;
  }

  &__sale {
    font-size: 18px;
    font-weight: 700;
  }

  &__actions {
    display: flex;
    gap: 6px;
    margin-top: 4px;
  }
}

.form {
  display: flex;
  flex-direction: column;
  gap: 12px;

  &__product {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    font-weight: 600;
  }

  &__preview {
    display: flex;
    flex-direction: column;
    gap: 4px;

    p {
      margin: 0;
    }
  }

  &__actions {
    display: flex;
    gap: 8px;
  }
}

@media (min-width: 1024px) {
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 380px;
    align-items: start;
  }
}
</style>
