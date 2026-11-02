<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '~/features/staff/auth/store'
import { useAdminCatalogStore } from '~/features/staff/catalog/store'
import { usePricingApi } from '~/features/staff/pricing/api'
import type { PricingRule } from '~/features/staff/pricing/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'
import { calcSalePrice } from '~/features/staff/pricing/calc'
import { formatPrice } from '~/shared/lib/format'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin'] })
useHead({ title: 'Наценка | Кабинет' })

const api = usePricingApi()
const auth = useAuthStore()
const catalog = useAdminCatalogStore()
const toast = useToast()

const rules = ref<PricingRule[]>([])
const isSaving = ref(false)
const loadError = ref('')

const form = reactive({ category_id: '' as number | '', markup_percent: '20', min_profit: '30' })
// Пример для наглядности: как правило сработает на дешёвом и дорогом товаре
const examples = computed(() =>
  [50, 1150].map((cost) => ({
    cost,
    price: calcSalePrice(cost, Number(form.markup_percent.replace(',', '.')) || 0, Number(form.min_profit.replace(',', '.')) || 0),
  })),
)

const defaultRule = computed(() => rules.value.find((rule) => rule.category_id === null) ?? null)
const categoryRules = computed(() => rules.value.filter((rule) => rule.category_id !== null))

function pick(rule: PricingRule | null) {
  Object.assign(form, {
    category_id: rule?.category_id ?? '',
    markup_percent: rule ? String(Number(rule.markup_percent)) : '20',
    min_profit: rule ? String(Number(rule.min_profit)) : '30',
  })
}

async function load() {
  try {
    rules.value = await api.listRules()
    pick(defaultRule.value)
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить правила')
  }
}

async function submit() {
  isSaving.value = true
  try {
    const result = await api.saveRule({
      category_id: form.category_id === '' ? null : Number(form.category_id),
      markup_percent: form.markup_percent.replace(',', '.'),
      min_profit: form.min_profit.replace(',', '.'),
    })
    toast.success(`Сохранено. Изменилось цен: ${result.updated_prices}`)
    rules.value = await api.listRules()
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSaving.value = false
  }
}

async function remove(rule: PricingRule) {
  const name = catalog.categoryNames.get(rule.category_id!) ?? 'категории'
  if (!confirm(`Удалить правило для «${name}»? Товары перейдут на общую наценку.`)) return
  try {
    await api.deleteRule(rule.id)
    rules.value = await api.listRules()
    toast.success('Правило удалено')
  } catch (error) {
    toast.error(errorMessage(error))
  }
}

onMounted(() => Promise.all([load(), catalog.loadCategories()]))
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <div>
        <h1 class="a-title">Наценка</h1>
        <p class="a-muted">Для товаров партнёра с автоматической ценой. Пересчёт сразу после сохранения и при каждом импорте.</p>
      </div>
    </div>

    <p v-if="loadError" class="a-error" role="alert">{{ loadError }}</p>

    <div class="layout">
      <div class="layout__rules">
        <section class="a-card">
          <h2 class="a-subtitle">Общая</h2>
          <p v-if="defaultRule" class="rule">
            <span class="rule__value">+{{ Number(defaultRule.markup_percent) }}%</span>
            <span class="a-muted">не меньше {{ formatPrice(defaultRule.min_profit) }} с единицы</span>
            <button v-if="auth.isAdmin" class="a-btn a-btn--ghost a-btn--small" type="button" @click="pick(defaultRule)">
              Изменить
            </button>
          </p>
          <p v-else class="a-error">
            Общая наценка не задана. Товары партнёра без правила продаются по закупочной цене.
          </p>
        </section>

        <section class="a-card">
          <h2 class="a-subtitle">По категориям</h2>
          <p v-if="!categoryRules.length" class="a-muted">Нет. Везде действует общая наценка.</p>
          <div v-for="rule in categoryRules" :key="rule.id" class="rule">
            <span class="rule__name">{{ catalog.categoryNames.get(rule.category_id!) }}</span>
            <span class="rule__value">+{{ Number(rule.markup_percent) }}%</span>
            <span class="a-muted">от {{ formatPrice(rule.min_profit) }}</span>
            <span v-if="auth.isAdmin" class="rule__actions">
              <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="pick(rule)">Изменить</button>
              <button class="a-btn a-btn--danger a-btn--small" type="button" @click="remove(rule)">Удалить</button>
            </span>
          </div>
        </section>
      </div>

      <form v-if="auth.isAdmin" class="a-card" @submit.prevent="submit">
        <h2 class="a-subtitle">Задать правило</h2>
        <label class="a-field">
          <span class="a-field__label">Категория</span>
          <select v-model="form.category_id" class="a-select">
            <option value="">Общая для всех</option>
            <option v-for="option in catalog.categoryOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
          </select>
        </label>
        <div class="a-grid a-grid--2">
          <label class="a-field">
            <span class="a-field__label">Наценка, %</span>
            <input v-model="form.markup_percent" class="a-input" inputmode="decimal" required pattern="\d{1,3}([.,]\d{1,2})?">
          </label>
          <label class="a-field">
            <span class="a-field__label">Минимум прибыли, ₽</span>
            <input v-model="form.min_profit" class="a-input" inputmode="decimal" required pattern="\d+([.,]\d{1,2})?">
          </label>
        </div>
        <p v-for="example in examples" :key="example.cost" class="a-muted">
          Закупка {{ formatPrice(example.cost) }} → продажа {{ formatPrice(example.price) }}
        </p>
        <button class="a-btn" type="submit" :disabled="isSaving">{{ isSaving ? 'Сохраняем…' : 'Сохранить и пересчитать' }}</button>
      </form>
      <section v-else class="a-card a-muted">Наценку меняет администратор.</section>
    </div>
  </div>
</template>

<style scoped lang="scss">
.layout {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__rules {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}

.rule {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 12px;

  & + & {
    padding-top: 12px;
    border-top: 1px solid var(--color-line);
  }

  &__name {
    flex-basis: 100%;
    font-weight: 600;
  }

  &__value {
    font-size: 18px;
    font-weight: 700;
  }

  &__actions {
    display: flex;
    gap: 6px;
    margin-left: auto;
  }
}

@media (min-width: 1024px) {
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 380px;
    align-items: start;
  }

  .rule__name {
    flex-basis: auto;
    min-width: 200px;
  }
}
</style>
