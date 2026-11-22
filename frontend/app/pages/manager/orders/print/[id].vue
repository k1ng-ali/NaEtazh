<script setup lang="ts">
import QRCode from 'qrcode'
import { computed, nextTick, onMounted, ref } from 'vue'
import { DELIVERY_SLOT, LIFTING } from '~/features/checkout/labels'
import { useShopPhone } from '~/features/legal/useShopPhone'
import { useStaffOrdersApi } from '~/features/staff/orders/api'
import type { OrderAdmin } from '~/features/staff/orders/types'
import { errorMessage } from '~/features/staff/shared/errors'
import BrandLogo from '~/shared/ui/BrandLogo.vue'
import { amountInWords } from '~/shared/lib/amount-in-words'
import { formatPrice, formatQuantity } from '~/shared/lib/format'
import { SELLER } from '~/shared/lib/legal'
import { useMediaUrl } from '~/shared/lib/media'

// Накладная к заказу на лист A4. Печатается из браузера, там же сохраняется в PDF
definePageMeta({ layout: false, middleware: 'staff', roles: ['admin', 'manager'] })

const api = useStaffOrdersApi()
const route = useRoute()
const mediaUrl = useMediaUrl()
const ordersPhone = await useShopPhone()
const { siteUrl } = useRuntimeConfig().public

const order = ref<OrderAdmin | null>(null)
const loadError = ref('')
const qr = ref('')

// Имя PDF при сохранении берётся из заголовка страницы
useHead(() => ({ title: order.value ? `Накладная № ${order.value.id}` : 'Накладная' }))

const dateFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
const shortDate = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })
const today = dateFormat.format(new Date())
const siteHost = computed(() => siteUrl.replace(/^https?:\/\//, '').replace(/\/$/, ''))

const delivery = computed(() => {
  if (!order.value) return ''
  const date = order.value.planned_date ?? order.value.delivery_date
  const slot = order.value.planned_slot ?? order.value.delivery_slot
  const day = date ? shortDate.format(new Date(`${date}T00:00:00`)) : 'Дата не согласована'
  return slot ? `${day}, ${DELIVERY_SLOT[slot].toLowerCase()}` : day
})

async function load() {
  try {
    order.value = await api.getOrder(Number(route.params.id))
    qr.value = await QRCode.toDataURL(`${siteUrl}/order/${order.value.public_token}`, {
      width: 320,
      margin: 0,
      errorCorrectionLevel: 'M',
    })
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить заказ')
  }
}

// Окно печати открываем, когда догрузятся фото: иначе в PDF будут пустые квадраты
async function waitForImages() {
  const pending = Array.from(document.querySelectorAll<HTMLImageElement>('.invoice img'))
    .filter((img) => !img.complete)
    .map(
      (img) =>
        new Promise<void>((done) => {
          img.addEventListener('load', () => done(), { once: true })
          img.addEventListener('error', () => done(), { once: true })
        }),
    )
  // Фото партнёра может не ответить: дольше 4 секунд не ждём
  await Promise.race([Promise.all(pending), new Promise((done) => setTimeout(done, 4000))])
}

function print() {
  window.print()
}

onMounted(async () => {
  await load()
  if (!order.value || route.query.auto !== '1') return
  await nextTick()
  await waitForImages()
  print()
})
</script>

<template>
  <div class="sheet-wrap">
    <div class="toolbar">
      <NuxtLink :to="order ? `/manager/orders/${order.id}` : '/manager/orders'" class="toolbar__back">← К заказу</NuxtLink>
      <button class="toolbar__print" type="button" :disabled="!order" @click="print">Печать или PDF</button>
    </div>

    <p v-if="loadError" class="state state--error" role="alert">{{ loadError }}</p>
    <p v-else-if="!order" class="state">Загружаем накладную…</p>

    <article v-else class="invoice">
      <header class="invoice__head">
        <div class="invoice__brand">
          <BrandLogo class="invoice__logo" />
          <p class="invoice__tagline">Стройматериалы с доставкой и подъёмом в квартиру</p>
        </div>
        <div class="invoice__title">
          <h1>Накладная № {{ order.id }}</h1>
          <p>от {{ today }}</p>
          <p class="muted">к заказу от {{ shortDate.format(new Date(order.created_at)) }}</p>
        </div>
      </header>

      <section class="parties">
        <div class="party">
          <h2>Продавец</h2>
          <p class="party__name">{{ SELLER.legalName }}</p>
          <p>ИНН {{ SELLER.inn }}, ОГРНИП {{ SELLER.ogrn }}</p>
          <p>Заказы: {{ ordersPhone }}</p>
          <p>{{ siteHost }}</p>
        </div>
        <div class="party">
          <h2>Покупатель</h2>
          <p class="party__name">{{ order.customer_name }}</p>
          <p>{{ order.customer_phone }}</p>
          <p>{{ order.address }}</p>
        </div>
        <div class="party">
          <h2>Доставка</h2>
          <p class="party__name">{{ delivery }}</p>
          <p>{{ LIFTING[order.lifting_type] }}</p>
          <p v-if="order.courier_name">Курьер: {{ order.courier_name }}</p>
        </div>
      </section>

      <div class="items-wrap">
        <table class="items">
          <thead>
            <tr>
              <th class="items__index">№</th>
              <th class="items__photo" aria-label="Фото" />
              <th>Наименование</th>
              <th class="num">Кол-во</th>
              <th>Ед.</th>
              <th class="num">Цена</th>
              <th class="num">Сумма</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(line, index) in order.lines" :key="line.id">
              <td class="items__index">{{ index + 1 }}</td>
              <td class="items__photo">
                <img v-if="line.image" :src="mediaUrl(line.image)" alt="">
              </td>
              <td class="items__name">{{ line.name }}</td>
              <td class="num">{{ formatQuantity(line.quantity) }}</td>
              <td>{{ line.unit }}</td>
              <td class="num">{{ formatPrice(line.unit_price) }}</td>
              <td class="num">{{ formatPrice(line.total) }}</td>
            </tr>
            <tr v-for="(service, index) in order.services" :key="`s${service.id}`" class="items__service">
              <td class="items__index">{{ order.lines.length + index + 1 }}</td>
              <td class="items__photo" />
              <td class="items__name">{{ service.name }}</td>
              <td class="num">1</td>
              <td>усл.</td>
              <td class="num">{{ formatPrice(service.price) }}</td>
              <td class="num">{{ Number(service.price) ? formatPrice(service.price) : 'Бесплатно' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <section class="summary">
        <div class="summary__words">
          <p>
            Всего наименований {{ order.lines.length + order.services.length }}, на сумму
            <strong>{{ formatPrice(order.total) }}</strong>
          </p>
          <p class="summary__amount">{{ amountInWords(order.total) }}</p>
          <p class="muted">Оплата наличными при получении.</p>
          <p v-if="order.comment" class="summary__comment">Комментарий покупателя: {{ order.comment }}</p>
        </div>
        <dl class="summary__totals">
          <dt>Товары</dt>
          <dd>{{ formatPrice(order.goods_total) }}</dd>
          <dt>Доставка и подъём</dt>
          <dd>{{ formatPrice(order.services_total) }}</dd>
          <dt class="summary__total">Итого к оплате</dt>
          <dd class="summary__total">{{ formatPrice(order.total) }}</dd>
        </dl>
      </section>

      <section class="signatures">
        <div class="signature">
          <p>Товар отпустил</p>
          <div class="signature__line"><span>подпись</span><span>расшифровка</span></div>
        </div>
        <div class="signature">
          <p>Товар получил, претензий к количеству и внешнему виду не имею</p>
          <div class="signature__line"><span>подпись</span><span>расшифровка</span></div>
        </div>
      </section>

      <footer class="invoice__foot">
        <img v-if="qr" :src="qr" alt="" class="invoice__qr">
        <div>
          <p class="party__name">Статус заказа онлайн</p>
          <p class="muted">Наведите камеру на QR-код или откройте ссылку из сообщения о заказе.</p>
          <p class="muted">Вопросы по заказу: {{ ordersPhone }}</p>
        </div>
      </footer>
    </article>
  </div>
</template>

<style scoped lang="scss">
// Документ всегда светлый и в своих цветах: так он одинаково выглядит на экране и на бумаге
$ink: #1a1a1a;
$muted: #6b6b6b;
$line: #d9d9d9;
$accent: #f6632d;

.sheet-wrap {
  min-height: 100vh;
  padding: 16px;
  background: #ececec;
  color: $ink;
  font-size: 13px;
  line-height: 1.4;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  max-width: 210mm;
  margin: 0 auto 12px;

  &__back {
    color: $ink;
  }

  &__print {
    height: 44px;
    padding-inline: 20px;
    border: 0;
    border-radius: 10px;
    background: $ink;
    color: #fff;
    font: inherit;
    font-weight: 600;
    cursor: pointer;

    &:disabled {
      opacity: 0.5;
    }
  }
}

.state {
  max-width: 210mm;
  margin: 0 auto;

  &--error {
    color: #c62828;
  }
}

.muted {
  color: $muted;
}

p {
  margin: 0;
}

.invoice {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 210mm;
  margin: 0 auto;
  padding: 14mm 12mm;
  background: #fff;
  box-shadow: 0 2px 16px rgb(0 0 0 / 10%);

  &__head {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding-bottom: 14px;
    border-bottom: 3px solid $accent;
  }

  &__logo {
    height: 30px;
    color: $ink;
  }

  &__tagline {
    margin-top: 6px;
    color: $muted;
    font-size: 12px;
  }

  &__title {
    text-align: right;

    h1 {
      margin: 0 0 2px;
      font-size: 22px;
      line-height: 1.2;
    }
  }

  &__foot {
    display: flex;
    align-items: center;
    gap: 14px;
    padding-top: 14px;
    border-top: 1px solid $line;
  }

  &__qr {
    width: 26mm;
    height: 26mm;
  }
}

.parties {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.party {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f6f6f6;

  h2 {
    margin: 0 0 4px;
    color: $muted;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  &__name {
    font-weight: 600;
  }
}

// С телефона таблица прокручивается вбок, на бумаге A4 она помещается целиком
.items-wrap {
  overflow-x: auto;
}

.items {
  width: 100%;
  min-width: 520px;
  border-collapse: collapse;

  th {
    padding: 8px 6px;
    border-bottom: 2px solid $ink;
    color: $muted;
    font-size: 11px;
    font-weight: 600;
    text-align: left;
    text-transform: uppercase;
    white-space: nowrap;
  }

  td {
    padding: 6px;
    border-bottom: 1px solid $line;
    vertical-align: middle;
  }

  tr {
    break-inside: avoid;
  }

  .num {
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }

  &__index {
    width: 24px;
    color: $muted;
  }

  &__photo {
    width: 40px;

    img {
      display: block;
      width: 36px;
      height: 36px;
      object-fit: contain;
    }
  }

  &__name {
    width: 100%;
  }

  &__service td {
    color: #3a3a3a;
  }
}

.summary {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 16px;
  break-inside: avoid;

  &__words {
    display: flex;
    flex: 1 1 260px;
    flex-direction: column;
    gap: 4px;
  }

  &__amount {
    font-weight: 600;
  }

  &__comment {
    margin-top: 6px;
    padding: 8px 10px;
    border-left: 3px solid $accent;
    background: #fff4ef;
  }

  &__totals {
    display: grid;
    grid-template-columns: auto auto;
    gap: 4px 24px;
    align-content: start;
    margin: 0;

    dt {
      color: $muted;
    }

    dd {
      margin: 0;
      text-align: right;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }
  }

  &__total {
    padding-top: 6px;
    border-top: 2px solid $ink;
    color: $ink !important;
    font-size: 16px;
    font-weight: 700;
  }
}

.signatures {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 24px;
  margin-top: 8px;
  break-inside: avoid;
}

.signature {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 28px;

  &__line {
    display: flex;
    justify-content: space-between;
    padding-top: 4px;
    border-top: 1px solid $ink;
    color: $muted;
    font-size: 10px;
  }
}

@media (max-width: 639px) {
  .sheet-wrap {
    padding: 12px;
  }

  .invoice {
    padding: 16px;

    &__title {
      text-align: left;
    }
  }
}

@page {
  size: A4;
  margin: 10mm;
}

@media print {
  .sheet-wrap {
    min-height: 0;
    padding: 0;
    background: #fff;
  }

  .toolbar {
    display: none;
  }

  .items-wrap {
    overflow: visible;
  }

  .items {
    min-width: 0;
  }

  .invoice {
    max-width: none;
    padding: 0;
    box-shadow: none;
  }

  // Браузеры по умолчанию не печатают фон: плашки и акценты должны остаться
  .invoice,
  .invoice * {
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }
}
</style>
