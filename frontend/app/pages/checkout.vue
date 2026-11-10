<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { GOAL, reachGoal } from '~/features/analytics/metrika'
import CartSummary from '~/features/cart/components/CartSummary.vue'
import { useCartStore } from '~/features/cart/store'
import { useQuoteSync } from '~/features/cart/useQuoteSync'
import { useCheckoutApi } from '~/features/checkout/api'
import { CONTACT_CHANNEL, DELIVERY_SLOT, LIFTING, MISSING_ITEM_POLICY } from '~/features/checkout/labels'
import type { ContactChannel, DeliverySlot, MissingItemPolicy } from '~/features/checkout/types'
import { useLocationStore } from '~/features/location/store'

useHead({ title: 'Оформление заказа | Строй База' })

const api = useCheckoutApi()
const cart = useCartStore()
const location = useLocationStore()
useQuoteSync()

if (!cart.items.length) await navigateTo('/cart', { replace: true })

onMounted(() => reachGoal(GOAL.checkoutStart))

const form = reactive({
  name: '',
  phone: '',
  addressText: '',
  deliveryDate: '',
  deliverySlot: 'morning' as DeliverySlot,
  contactChannel: 'call' as ContactChannel,
  missingPolicy: 'call' as MissingItemPolicy,
  comment: '',
  consent: false,
})
const isSubmitting = ref(false)
const errorText = ref('')

// Ближайшая неделя, начиная с завтра: точную дату подтвердит менеджер
const dateFormat = new Intl.DateTimeFormat('ru-RU', { weekday: 'short', day: 'numeric', month: 'long' })
const dates = computed(() =>
  Array.from({ length: 7 }, (_, index) => {
    const date = new Date()
    date.setDate(date.getDate() + index + 1)
    const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    return { value, label: dateFormat.format(date) }
  }),
)

const ERRORS: Record<string, string> = {
  'Not enough stock': 'Пока вы оформляли, часть товаров закончилась. Проверьте корзину',
  'Product unavailable': 'Один из товаров сняли с продажи, мы убрали его из корзины. Проверьте итог',
  'Address is required': 'Укажите адрес доставки',
  'Delivery date is in the past': 'Выберите другую дату доставки',
}

async function submit() {
  if (!cart.quote?.can_order) return
  isSubmitting.value = true
  errorText.value = ''
  try {
    const created = await api.createOrder({
      ...cart.payload(),
      customer_name: form.name.trim(),
      customer_phone: form.phone,
      contact_channel: form.contactChannel,
      missing_item_policy: form.missingPolicy,
      address_text: location.building ? null : form.addressText.trim(),
      entrance: location.entrance.trim() || null,
      apartment: location.apartment.trim() || null,
      delivery_date: form.deliveryDate || null,
      delivery_slot: form.deliverySlot,
      comment: form.comment.trim() || null,
      source_code: location.sourceCode,
      consent: true,
    })
    // Сумма в цели даёт доход по корпусам в отчётах Метрики
    reachGoal(GOAL.orderCreated, { order_price: Number(cart.quote?.total ?? 0), currency: 'RUB' })
    cart.clear()
    await navigateTo(`/order/${created.public_token}?new=1`)
  } catch (error) {
    const data = (error as { data?: { detail?: unknown } })?.data
    if (typeof data?.detail === 'string') {
      errorText.value = ERRORS[data.detail] ?? 'Не удалось оформить заказ. Попробуйте ещё раз'
      await cart.refreshQuote()
    } else if (Array.isArray(data?.detail)) {
      errorText.value = 'Проверьте номер телефона: нужен мобильный, например +7 912 345-67-89'
    } else {
      errorText.value = 'Нет связи с сервером. Корзина сохранена, попробуйте ещё раз'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="container checkout">
    <NuxtLink to="/cart" class="muted checkout__back">← Корзина</NuxtLink>
    <h1 class="checkout__title">Оформление заказа</h1>

    <form class="checkout__layout" @submit.prevent="submit">
      <div class="checkout__main">
        <section class="card checkout__section">
          <h2 class="checkout__subtitle">Контакты</h2>
          <label class="field">
            <span class="field__label">Имя</span>
            <input v-model="form.name" class="input" autocomplete="given-name" required maxlength="80">
          </label>
          <label class="field">
            <span class="field__label">Телефон</span>
            <input
              v-model="form.phone"
              class="input"
              type="tel"
              autocomplete="tel"
              inputmode="tel"
              placeholder="+7 912 345-67-89"
              required
              maxlength="20"
            >
          </label>
          <div class="field">
            <span class="field__label">Как удобнее связаться</span>
            <div class="checkout__chips">
              <label v-for="(label, value) in CONTACT_CHANNEL" :key="value" class="chip" :class="{ 'is-active': form.contactChannel === value }">
                <input v-model="form.contactChannel" type="radio" name="channel" :value="value">
                {{ label }}
              </label>
            </div>
          </div>
        </section>

        <section class="card checkout__section">
          <h2 class="checkout__subtitle">Адрес</h2>
          <div v-if="location.building" class="checkout__building">
            <strong>{{ location.building.complex_name }}, {{ location.building.name }}</strong>
            <span v-if="location.building.complex_address" class="muted">{{ location.building.complex_address }}</span>
            <button class="checkout__change" type="button" @click="location.clearBuilding()">Другой адрес</button>
          </div>
          <label v-else class="field">
            <span class="field__label">Улица и дом</span>
            <input v-model="form.addressText" class="input" autocomplete="street-address" required maxlength="250">
          </label>
          <div class="checkout__row">
            <label class="field">
              <span class="field__label">Подъезд</span>
              <input v-model="location.entrance" class="input" inputmode="numeric" maxlength="10">
            </label>
            <label class="field">
              <span class="field__label">Этаж</span>
              <input
                class="input"
                type="number"
                inputmode="numeric"
                min="1"
                :value="location.floor ?? ''"
                @change="location.floor = Number(($event.target as HTMLInputElement).value) || null"
              >
            </label>
            <label class="field">
              <span class="field__label">Квартира</span>
              <input
                v-model="location.apartment"
                class="input"
                inputmode="numeric"
                maxlength="10"
                :required="Boolean(location.building)"
              >
            </label>
          </div>
          <p class="muted checkout__hint">{{ LIFTING[cart.liftingType] }}. Изменить можно в корзине</p>
        </section>

        <section class="card checkout__section">
          <h2 class="checkout__subtitle">Когда привезти</h2>
          <div class="checkout__row checkout__row--2">
            <label class="field">
              <span class="field__label">День</span>
              <select v-model="form.deliveryDate" class="input">
                <option value="">Как можно скорее</option>
                <option v-for="date in dates" :key="date.value" :value="date.value">{{ date.label }}</option>
              </select>
            </label>
            <label class="field">
              <span class="field__label">Время</span>
              <select v-model="form.deliverySlot" class="input">
                <option v-for="(label, value) in DELIVERY_SLOT" :key="value" :value="value">{{ label }}</option>
              </select>
            </label>
          </div>
          <p class="muted checkout__hint">Менеджер позвонит и подтвердит время</p>
          <label class="field">
            <span class="field__label">Если какого-то товара не окажется</span>
            <select v-model="form.missingPolicy" class="input">
              <option v-for="(label, value) in MISSING_ITEM_POLICY" :key="value" :value="value">{{ label }}</option>
            </select>
          </label>
          <label class="field">
            <span class="field__label">Комментарий</span>
            <textarea v-model="form.comment" class="input" maxlength="1000" placeholder="Например, позвонить за час" />
          </label>
        </section>
      </div>

      <aside class="checkout__side">
        <CartSummary :quote="cart.quote" :is-quoting="cart.isQuoting">
          <label class="checkout__consent">
            <input v-model="form.consent" type="checkbox" required>
            <span>
              Даю <NuxtLink to="/legal/consent" target="_blank" class="checkout__doc">согласие на обработку персональных данных</NuxtLink>
              для доставки заказа на условиях <NuxtLink to="/legal/privacy" target="_blank" class="checkout__doc">политики</NuxtLink>
            </span>
          </label>
          <p v-if="errorText" class="error-text" role="alert">{{ errorText }}</p>
          <button
            class="btn btn--block btn--large"
            type="submit"
            :disabled="isSubmitting || cart.isQuoting || !cart.quote?.can_order"
          >
            {{ isSubmitting ? 'Отправляем…' : 'Подтвердить заказ' }}
          </button>
        </CartSummary>
      </aside>
    </form>
  </div>
</template>

<style scoped lang="scss">
.checkout {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__back {
    align-self: flex-start;
  }

  &__title {
    font-size: 22px;
    font-weight: 700;
  }

  &__layout,
  &__main,
  &__side {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  &__section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__subtitle {
    font-size: 17px;
    font-weight: 600;
  }

  &__row {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;

    &--2 {
      grid-template-columns: minmax(0, 1fr);
    }
  }

  &__chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  &__building {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }

  &__change {
    min-height: var(--tap-size);
    padding: 0;
    border: 0;
    background: transparent;
    color: var(--color-text);
    font-size: 15px;
    text-decoration: underline;
    cursor: pointer;
  }

  &__hint {
    font-size: 14px;
  }

  &__consent {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 14px;
    cursor: pointer;

    input {
      flex-shrink: 0;
      width: 20px;
      height: 20px;
      margin: 0;
      accent-color: var(--color-text);
    }
  }

  &__doc {
    text-decoration: underline;
  }
}

.chip {
  display: inline-flex;
  align-items: center;
  min-height: var(--tap-size);
  padding: 0 14px;
  border: 1.5px solid var(--color-line);
  border-radius: var(--radius-control);
  cursor: pointer;

  &.is-active {
    border-color: var(--color-text);
    font-weight: 600;
  }

  input {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }

  &:focus-within {
    outline: 2px solid var(--color-text);
    outline-offset: 2px;
  }
}

@media (min-width: 640px) {
  .checkout__row--2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (min-width: 1024px) {
  .checkout {
    &__title {
      font-size: 28px;
    }

    &__layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 360px;
      align-items: start;
      gap: 24px;
    }

    &__side {
      position: sticky;
      top: 96px;
    }
  }
}
</style>
