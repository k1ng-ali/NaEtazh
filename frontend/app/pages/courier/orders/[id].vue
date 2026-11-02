<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useCourierApi } from '~/features/courier/api'
import type { CourierOrder } from '~/features/courier/types'
import { DELIVERY_SLOT, LIFTING, ORDER_STATUS } from '~/features/checkout/labels'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'
import { formatDateTime, formatPrice, formatQuantity } from '~/shared/lib/format'

definePageMeta({ layout: 'courier', middleware: 'staff', roles: ['courier'] })

const api = useCourierApi()
const toast = useToast()
const route = useRoute()

const order = ref<CourierOrder | null>(null)
const loadError = ref('')
const isSaving = ref(false)
// Отметки при погрузке живут только на телефоне курьера
const loaded = reactive<Record<number, boolean>>({})
const cash = ref('')
const isDelivering = ref(false)
const problem = ref('')
const isProblemOpen = ref(false)

useHead(() => ({ title: order.value ? `Заказ № ${order.value.id} | Доставки` : 'Доставки' }))

const phoneDigits = computed(() => order.value?.customer_phone.replace(/\D/g, '') ?? '')
const mapUrl = computed(() =>
  order.value?.map_address ? `https://yandex.ru/maps/?text=${encodeURIComponent(order.value.map_address)}` : null,
)
const dateFormat = new Intl.DateTimeFormat('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })
const when = computed(() => {
  if (!order.value) return ''
  const day = order.value.planned_date ? dateFormat.format(new Date(`${order.value.planned_date}T00:00:00`)) : 'Дата не согласована'
  return order.value.planned_slot ? `${day}, ${DELIVERY_SLOT[order.value.planned_slot].toLowerCase()}` : day
})
const allLoaded = computed(() => Boolean(order.value?.lines.length) && order.value!.lines.every((_, index) => loaded[index]))

function apply(value: CourierOrder) {
  order.value = value
  cash.value = String(Number(value.total))
}

async function load() {
  try {
    apply(await api.getOrder(Number(route.params.id)))
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить заказ')
  }
}

async function run(action: () => Promise<CourierOrder>, success: string) {
  isSaving.value = true
  try {
    apply(await action())
    toast.success(success)
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSaving.value = false
  }
}

const start = () => run(() => api.start(order.value!.id), 'Хорошей дороги')

async function deliver() {
  const value = cash.value.trim().replace(',', '.')
  if (!/^\d+(\.\d{1,2})?$/.test(value)) return toast.error('Введите сумму цифрами')
  if (Number(value) !== Number(order.value!.total) && !confirm(`Получено ${value} ₽, а по заказу ${Number(order.value!.total)} ₽. Всё верно?`)) return
  await run(() => api.deliver(order.value!.id, value), 'Заказ доставлен')
  isDelivering.value = false
}

async function sendProblem() {
  if (!problem.value.trim()) return
  await run(() => api.reportProblem(order.value!.id, problem.value.trim()), 'Менеджер получил сообщение')
  problem.value = ''
  isProblemOpen.value = false
}

onMounted(load)
</script>

<template>
  <div class="order">
    <NuxtLink to="/courier" class="a-muted">← Все доставки</NuxtLink>
    <p v-if="loadError" class="a-error" role="alert">{{ loadError }}</p>
    <p v-else-if="!order" class="a-muted">Загружаем…</p>

    <template v-else>
      <div class="order__head">
        <h1 class="a-title">Заказ № {{ order.id }}</h1>
        <span class="a-badge" :class="{ 'a-badge--success': order.status === 'delivered', 'a-badge--warning': order.status === 'in_delivery' }">
          {{ ORDER_STATUS[order.status] }}
        </span>
      </div>

      <section class="a-card">
        <p class="order__address">{{ order.address }}</p>
        <p class="a-muted">{{ when }}</p>
        <p>{{ LIFTING[order.lifting_type] }}</p>
        <div class="order__buttons">
          <a :href="`tel:${order.customer_phone}`" class="a-btn">Позвонить</a>
          <a v-if="mapUrl" :href="mapUrl" target="_blank" rel="noopener" class="a-btn a-btn--ghost">Маршрут</a>
          <a
            v-if="order.contact_channel === 'whatsapp'"
            :href="`https://wa.me/${phoneDigits}`"
            target="_blank"
            rel="noopener"
            class="a-btn a-btn--ghost"
          >
            WhatsApp
          </a>
        </div>
        <p class="a-muted">{{ order.customer_name }}, {{ order.customer_phone }}</p>
        <p v-if="order.comment" class="order__comment">{{ order.comment }}</p>
      </section>

      <section class="a-card">
        <h2 class="a-subtitle">Погрузка</h2>
        <label v-for="(line, index) in order.lines" :key="index" class="a-check order__line">
          <input v-model="loaded[index]" type="checkbox">
          <span>
            {{ line.name }}
            <strong>{{ formatQuantity(line.quantity) }} {{ line.unit }}</strong>
          </span>
        </label>
        <p v-if="allLoaded" class="order__ok">Всё погружено</p>
      </section>

      <section class="a-card order__money">
        <span>Получить наличными</span>
        <strong>{{ formatPrice(order.total) }}</strong>
        <p v-if="order.cash_received !== null" class="a-muted">
          Получено {{ formatPrice(order.cash_received) }}{{ order.delivered_at ? `, ${formatDateTime(order.delivered_at)}` : '' }}
        </p>
      </section>

      <!-- Главное действие всегда одно и крупное -->
      <div class="order__actions">
        <button v-if="order.status === 'confirmed'" class="a-btn order__main" type="button" :disabled="isSaving" @click="start">
          Выехал
        </button>

        <template v-if="order.status === 'in_delivery'">
          <form v-if="isDelivering" class="a-card" @submit.prevent="deliver">
            <label class="a-field">
              <span class="a-field__label">Сколько получено наличными, ₽</span>
              <input v-model="cash" class="a-input order__cash" inputmode="decimal" required>
            </label>
            <button class="a-btn order__main" type="submit" :disabled="isSaving">Подтвердить доставку</button>
            <button class="a-btn a-btn--ghost" type="button" @click="isDelivering = false">Отмена</button>
          </form>
          <button v-else class="a-btn order__main" type="button" @click="isDelivering = true">Доставлен</button>
        </template>

        <template v-if="order.status === 'confirmed' || order.status === 'in_delivery'">
          <form v-if="isProblemOpen" class="a-card" @submit.prevent="sendProblem">
            <label class="a-field">
              <span class="a-field__label">Что случилось</span>
              <textarea v-model="problem" class="a-textarea" maxlength="500" required placeholder="Не отвечает телефон, домофон не работает…" />
            </label>
            <button class="a-btn" type="submit" :disabled="isSaving">Отправить менеджеру</button>
            <button class="a-btn a-btn--ghost" type="button" @click="isProblemOpen = false">Отмена</button>
          </form>
          <button v-else class="a-btn a-btn--danger" type="button" @click="isProblemOpen = true">Сообщить о проблеме</button>
        </template>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.order {
  display: flex;
  flex-direction: column;
  gap: 14px;

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  &__address {
    font-size: 20px;
    font-weight: 700;
  }

  &__buttons {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 8px;

    .a-btn {
      min-height: 52px;
    }
  }

  &__comment {
    padding: 10px 12px;
    border-radius: var(--radius-control);
    background: var(--color-bg);
  }

  &__line {
    align-items: flex-start;
    padding: 6px 0;

    input {
      flex-shrink: 0;
      margin-top: 2px;
    }
  }

  &__ok {
    color: var(--color-success);
    font-weight: 600;
  }

  &__money {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: baseline;
    justify-content: space-between;

    strong {
      font-size: 26px;
      font-variant-numeric: tabular-nums;
    }

    p {
      flex-basis: 100%;
    }
  }

  &__actions {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  &__main {
    min-height: 60px;
    font-size: 19px;
  }

  &__cash {
    min-height: 56px;
    font-size: 22px;
    font-weight: 700;
  }
}
</style>
