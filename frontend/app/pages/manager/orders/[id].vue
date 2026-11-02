<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '~/features/staff/auth/store'
import { useStaffOrdersApi } from '~/features/staff/orders/api'
import OrderDeliveryForm from '~/features/staff/orders/components/OrderDeliveryForm.vue'
import OrderHistory from '~/features/staff/orders/components/OrderHistory.vue'
import OrderStatusBadge from '~/features/staff/orders/components/OrderStatusBadge.vue'
import type { Courier, DeliveryPayload, OrderAdmin, OrderMoney, ServiceLineAdmin } from '~/features/staff/orders/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'
import { CONTACT_CHANNEL, DELIVERY_SLOT, LIFTING, MISSING_ITEM_POLICY } from '~/features/checkout/labels'
import type { OrderStatus } from '~/features/checkout/types'
import { formatDateTime, formatPrice, formatQuantity } from '~/shared/lib/format'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin', 'manager'] })

const api = useStaffOrdersApi()
const auth = useAuthStore()
const toast = useToast()
const route = useRoute()
const { siteUrl } = useRuntimeConfig().public

const order = ref<OrderAdmin | null>(null)
const couriers = ref<Courier[]>([])
// Деньги заказа приходят только владельцу
const money = computed(() => (order.value && 'profit' in order.value ? (order.value as OrderMoney) : null))
const loadError = ref('')
const isSaving = ref(false)
const costs = reactive<Record<number, string>>({})

useHead(() => ({ title: order.value ? `Заказ № ${order.value.id} | Кабинет` : 'Заказ | Кабинет' }))

// Подпись кнопки — действие, а не название статуса
const ACTIONS: Record<OrderStatus, string> = {
  new: '',
  checking: 'Проверяю наличие',
  confirmed: 'Подтвердить',
  in_delivery: 'Отправить',
  delivered: 'Доставлен',
  canceled: 'Отменить заказ',
}

const dateFormat = new Intl.DateTimeFormat('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' })
const deliveryWhen = computed(() => {
  if (!order.value) return ''
  const day = order.value.delivery_date ? dateFormat.format(new Date(`${order.value.delivery_date}T00:00:00`)) : 'Как можно скорее'
  return order.value.delivery_slot ? `${day}, ${DELIVERY_SLOT[order.value.delivery_slot].toLowerCase()}` : day
})
const phoneDigits = computed(() => order.value?.customer_phone.replace(/\D/g, '') ?? '')
const statusUrl = computed(() => (order.value ? `${siteUrl}/order/${order.value.public_token}` : ''))

function apply(value: OrderAdmin) {
  order.value = value
  for (const service of value.services) costs[service.id] = service.cost ?? ''
}

// Владельцу после любого действия перечитываем заказ с деньгами
async function reload(id: number) {
  apply(auth.isAdmin ? await api.getOrderMoney(id) : await api.getOrder(id))
}

async function load() {
  try {
    const id = Number(route.params.id)
    const [, list] = await Promise.all([reload(id), api.listCouriers()])
    couriers.value = list
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить заказ')
  }
}

async function changeStatus(status: OrderStatus) {
  if (!order.value) return
  if (status === 'canceled' && !confirm('Отменить заказ? Резерв на складе снимется.')) return
  isSaving.value = true
  try {
    const updated = await api.changeStatus(order.value.id, status)
    auth.isAdmin ? await reload(updated.id) : apply(updated)
    toast.success('Статус изменён')
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSaving.value = false
  }
}

async function saveDelivery(payload: DeliveryPayload) {
  if (!order.value) return
  isSaving.value = true
  try {
    const updated = await api.setDelivery(order.value.id, payload)
    auth.isAdmin ? await reload(updated.id) : apply(updated)
    toast.success('Доставка сохранена')
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSaving.value = false
  }
}

async function saveCost(service: ServiceLineAdmin) {
  if (!order.value) return
  const raw = (costs[service.id] ?? '').trim().replace(',', '.')
  if (raw === (service.cost ?? '')) return
  try {
    apply(await api.setServiceCost(order.value.id, service.id, raw || null))
    toast.success('Расход сохранён')
  } catch (error) {
    toast.error(errorMessage(error))
  }
}

async function copyStatusLink() {
  try {
    await navigator.clipboard.writeText(statusUrl.value)
    toast.success('Ссылка скопирована')
  } catch {
    toast.error('Не удалось скопировать, выделите ссылку вручную')
  }
}

onMounted(load)
</script>

<template>
  <div class="a-page">
    <NuxtLink to="/manager/orders" class="a-muted back">← Все заказы</NuxtLink>
    <p v-if="loadError" class="a-error" role="alert">{{ loadError }}</p>
    <p v-else-if="!order" class="a-muted">Загружаем…</p>

    <template v-else>
      <div class="a-page-head">
        <div>
          <h1 class="a-title">Заказ № {{ order.id }}</h1>
          <p class="a-muted">Создан {{ formatDateTime(order.created_at) }}</p>
        </div>
        <OrderStatusBadge :status="order.status" />
      </div>

      <div v-if="order.next_statuses.length" class="actions">
        <button
          v-for="status in order.next_statuses"
          :key="status"
          class="a-btn"
          :class="{ 'a-btn--danger': status === 'canceled' }"
          type="button"
          :disabled="isSaving"
          @click="changeStatus(status)"
        >
          {{ ACTIONS[status] }}
        </button>
      </div>

      <div class="layout">
        <div class="layout__main">
          <OrderDeliveryForm
            v-if="!['delivered', 'canceled'].includes(order.status)"
            :order="order"
            :couriers="couriers"
            :is-saving="isSaving"
            @save="saveDelivery"
          />
          <section v-else-if="order.status === 'delivered'" class="a-card">
            <h2 class="a-subtitle">Доставлен</h2>
            <p>
              {{ order.delivered_at ? formatDateTime(order.delivered_at) : '' }}
              <template v-if="order.courier_name">, {{ order.courier_name }}</template>
            </p>
            <p v-if="order.cash_received !== null" :class="{ 'a-error': Number(order.cash_received) !== Number(order.total) }">
              Получено наличными: {{ formatPrice(order.cash_received) }} из {{ formatPrice(order.total) }}
            </p>
          </section>

          <section class="a-card">
            <h2 class="a-subtitle">Состав</h2>
            <div v-for="line in order.lines" :key="line.id" class="line">
              <div class="line__head">
                <NuxtLink :to="`/manager/products/${line.product_id}`" class="line__name">{{ line.name }}</NuxtLink>
                <strong class="line__total">{{ formatPrice(line.total) }}</strong>
              </div>
              <span class="a-muted">{{ formatQuantity(line.quantity) }} {{ line.unit }} × {{ formatPrice(line.unit_price) }}</span>
              <ul class="line__sources">
                <li v-for="(allocation, index) in line.allocations" :key="index">
                  <span class="a-badge" :class="allocation.source_type === 'warehouse' ? 'a-badge--success' : 'a-badge--warning'">
                    {{ allocation.source_name }}
                  </span>
                  {{ formatQuantity(allocation.quantity) }} {{ line.unit }}
                  <span class="a-muted">
                    · закупка {{ allocation.unit_cost ? formatPrice(allocation.unit_cost) : 'не указана' }}
                  </span>
                  <a v-if="allocation.source_url" :href="allocation.source_url" target="_blank" rel="noopener noreferrer" class="line__link">
                    проверить у партнёра
                  </a>
                </li>
              </ul>
            </div>
          </section>

          <section class="a-card">
            <h2 class="a-subtitle">Услуги</h2>
            <p v-if="!order.services.length" class="a-muted">Тариф не был задан: стоимость доставки обсудите с покупателем.</p>
            <div v-for="service in order.services" :key="service.id" class="service">
              <span class="service__name">{{ service.name }}</span>
              <span class="service__price">{{ formatPrice(service.price) }}</span>
              <label v-if="money" class="a-field service__cost">
                <span class="a-field__label">Наш расход, ₽</span>
                <input
                  v-model="costs[service.id]"
                  class="a-input"
                  inputmode="decimal"
                  pattern="\d+([.,]\d{1,2})?"
                  @change="saveCost(service)"
                >
              </label>
            </div>
          </section>
        </div>

        <aside class="layout__side">
          <section class="a-card">
            <h2 class="a-subtitle">Покупатель</h2>
            <p class="contact__name">{{ order.customer_name }}</p>
            <div class="contact__links">
              <a :href="`tel:${order.customer_phone}`" class="a-btn a-btn--ghost">{{ order.customer_phone }}</a>
              <a v-if="order.contact_channel === 'whatsapp'" :href="`https://wa.me/${phoneDigits}`" target="_blank" rel="noopener" class="a-btn a-btn--ghost">
                WhatsApp
              </a>
            </div>
            <dl class="info">
              <dt>Связь</dt>
              <dd>{{ order.contact_channel ? CONTACT_CHANNEL[order.contact_channel] : '—' }}</dd>
              <dt>Если нет товара</dt>
              <dd>{{ order.missing_item_policy ? MISSING_ITEM_POLICY[order.missing_item_policy] : '—' }}</dd>
            </dl>
          </section>

          <section class="a-card">
            <h2 class="a-subtitle">Адрес</h2>
            <dl class="info">
              <dt>Адрес</dt>
              <dd>{{ order.address }}</dd>
              <dt>Просил</dt>
              <dd>{{ deliveryWhen }}</dd>
              <dt>Подъём</dt>
              <dd>{{ LIFTING[order.lifting_type] }}</dd>
              <template v-if="order.comment">
                <dt>Комментарий</dt>
                <dd>{{ order.comment }}</dd>
              </template>
              <template v-if="order.source_code">
                <dt>Пришёл по QR</dt>
                <dd>{{ order.source_code }}</dd>
              </template>
            </dl>
          </section>

          <section class="a-card">
            <h2 class="a-subtitle">{{ money ? 'Деньги' : 'Сумма' }}</h2>
            <dl class="money">
              <dt>Товары</dt>
              <dd>{{ formatPrice(order.goods_total) }}</dd>
              <dt>Услуги</dt>
              <dd>{{ formatPrice(order.services_total) }}</dd>
              <dt>Получить с покупателя</dt>
              <dd class="money__strong">{{ formatPrice(order.total) }}</dd>
              <template v-if="money">
                <dt>Закупка товаров</dt>
                <dd>− {{ formatPrice(money.goods_cost) }}</dd>
                <dt>Расход на услуги</dt>
                <dd>− {{ formatPrice(money.services_cost) }}</dd>
                <dt>Прибыль</dt>
                <dd class="money__strong">{{ formatPrice(money.profit) }}</dd>
              </template>
            </dl>
            <p v-if="money && !money.profit_complete" class="a-field__hint">
              Не у всех товаров или услуг указана себестоимость, прибыль приблизительная
            </p>
          </section>

          <OrderHistory :events="order.events" />

          <section class="a-card">
            <h2 class="a-subtitle">Ссылка для покупателя</h2>
            <p class="a-muted status-link">{{ statusUrl }}</p>
            <button class="a-btn a-btn--ghost" type="button" @click="copyStatusLink">Скопировать</button>
          </section>
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped lang="scss">
.back {
  align-self: flex-start;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.layout {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__main,
  &__side {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}

.line {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-line);

  &:last-child {
    padding-bottom: 0;
    border-bottom: 0;
  }

  &__head {
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }

  &__name {
    font-weight: 600;

    &:hover {
      text-decoration: underline;
    }
  }

  &__total {
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  &__sources {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin: 4px 0 0;
    padding: 0;
    list-style: none;
    font-size: 14px;
  }

  &__link {
    margin-left: 4px;
    text-decoration: underline;
  }
}

.service {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px 12px;
  align-items: center;

  &__price {
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }

  &__cost {
    grid-column: 1 / -1;
    max-width: 200px;
  }
}

.contact {
  &__name {
    font-size: 17px;
    font-weight: 600;
  }

  &__links {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
}

.info,
.money {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr);
  gap: 8px 12px;
  margin: 0;

  dt {
    color: var(--color-text-muted);
    font-size: 14px;
  }

  dd {
    margin: 0;
  }
}

.money {
  dd {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  &__strong {
    font-weight: 700;
  }
}

.status-link {
  overflow-wrap: anywhere;
  font-size: 13px;
}

@media (min-width: 640px) {
  .service {
    grid-template-columns: minmax(0, 1fr) auto 180px;

    &__cost {
      grid-column: auto;
    }
  }
}

@media (min-width: 1024px) {
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 380px;
    align-items: start;
    gap: 24px;
  }
}
</style>
