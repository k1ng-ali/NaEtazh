<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useLocationStore } from '~/features/location/store'
import { PRICE_ON_CALL, telHref, useServicesApi } from '~/features/services/api'

const route = useRoute()
const api = useServicesApi()
const location = useLocationStore()
const slug = computed(() => String(route.params.slug))

const { data: service, error } = await useAsyncData(`service-${slug.value}`, () => api.getService(slug.value))
if (error.value) {
  throw createError({ statusCode: 404, statusMessage: 'Услуга не найдена', fatal: true })
}

useHead({ title: () => `${service.value?.name ?? 'Услуга'} | Строй База` })

const form = reactive({
  name: '',
  phone: '',
  addressText: '',
  date: '',
  comment: '',
  consent: false,
})
const isSubmitting = ref(false)
const errorText = ref('')
const createdNumber = ref<number | null>(null)

// Две недели вперёд, начиная с завтра: точное время согласует менеджер
const dateFormat = new Intl.DateTimeFormat('ru-RU', { weekday: 'short', day: 'numeric', month: 'long' })
const dates = computed(() =>
  Array.from({ length: 14 }, (_, index) => {
    const date = new Date()
    date.setDate(date.getDate() + index + 1)
    const value = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    return { value, label: dateFormat.format(date) }
  }),
)

const ERRORS: Record<string, string> = {
  'Address is required': 'Укажите адрес',
  'Date is in the past': 'Выберите другую дату',
  'Service not found': 'Эта услуга сейчас недоступна',
}

async function submit() {
  if (!service.value) return
  isSubmitting.value = true
  errorText.value = ''
  try {
    const created = await api.createRequest({
      service_slug: service.value.slug,
      customer_name: form.name.trim(),
      customer_phone: form.phone,
      building_code: location.building?.code ?? null,
      address_text: location.building ? null : form.addressText.trim(),
      apartment: location.apartment.trim() || null,
      preferred_date: form.date || null,
      comment: form.comment.trim() || null,
      source_code: location.sourceCode,
      consent: true,
    })
    createdNumber.value = created.number
  } catch (failure) {
    const data = (failure as { data?: { detail?: unknown }; statusCode?: number })
    if (data.statusCode === 429) {
      errorText.value = 'Слишком много заявок подряд. Подождите минуту'
    } else if (typeof data.data?.detail === 'string') {
      errorText.value = ERRORS[data.data.detail] ?? 'Не удалось отправить заявку. Попробуйте ещё раз'
    } else if (Array.isArray(data.data?.detail)) {
      errorText.value = 'Проверьте номер телефона: нужен мобильный, например +7 912 345-67-89'
    } else {
      errorText.value = 'Нет связи с сервером. Попробуйте ещё раз'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div v-if="service" class="container service">
    <NuxtLink to="/services" class="muted service__back">← Все услуги</NuxtLink>
    <h1 class="service__title">{{ service.name }}</h1>

    <section class="card service__about">
      <p v-if="service.description" class="service__text">{{ service.description }}</p>
      <p class="service__price">{{ service.price_text ?? PRICE_ON_CALL }}</p>
      <a v-if="service.phone" :href="telHref(service.phone)" class="btn btn--ghost service__call">
        Позвонить: {{ service.phone }}
      </a>
    </section>

    <section v-if="createdNumber" class="card service__done" role="status">
      <h2 class="service__subtitle">Заявка № {{ createdNumber }} принята</h2>
      <p>Менеджер перезвонит, уточнит детали и назовёт цену.</p>
      <NuxtLink to="/services" class="btn btn--ghost">Другие услуги</NuxtLink>
    </section>

    <form v-else class="card service__form" @submit.prevent="submit">
      <h2 class="service__subtitle">Оставить заявку</h2>
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

      <ClientOnly>
        <div v-if="location.building" class="service__building">
          <strong>{{ location.building.complex_name }}, {{ location.building.name }}</strong>
          <button class="service__change" type="button" @click="location.clearBuilding()">Другой адрес</button>
        </div>
        <label v-else class="field">
          <span class="field__label">Адрес</span>
          <input v-model="form.addressText" class="input" autocomplete="street-address" required maxlength="250">
        </label>
      </ClientOnly>
      <label class="field">
        <span class="field__label">Квартира</span>
        <input v-model="location.apartment" class="input" inputmode="numeric" maxlength="10">
      </label>
      <label class="field">
        <span class="field__label">Когда удобно</span>
        <select v-model="form.date" class="input">
          <option value="">Как можно скорее</option>
          <option v-for="date in dates" :key="date.value" :value="date.value">{{ date.label }}</option>
        </select>
      </label>
      <label class="field">
        <span class="field__label">Что нужно сделать</span>
        <textarea
          v-model="form.comment"
          class="input service__textarea"
          maxlength="1000"
          placeholder="Например, 20 мешков мусора, 9 этаж, есть грузовой лифт"
        />
      </label>

      <label class="service__consent">
        <input v-model="form.consent" type="checkbox" required>
        <span>
          Даю <NuxtLink to="/legal/consent" target="_blank" class="service__doc">согласие на обработку персональных данных</NuxtLink>
          для обработки заявки на условиях <NuxtLink to="/legal/privacy" target="_blank" class="service__doc">политики</NuxtLink>
        </span>
      </label>
      <p v-if="errorText" class="error-text" role="alert">{{ errorText }}</p>
      <button class="btn btn--block btn--large" type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Отправляем…' : 'Отправить заявку' }}
      </button>
    </form>
  </div>
</template>

<style scoped lang="scss">
.service {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 640px;

  &__back {
    align-self: flex-start;
  }

  &__title {
    font-size: 22px;
    font-weight: 700;
  }

  &__about,
  &__form,
  &__done {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__text {
    white-space: pre-line;
  }

  &__price {
    font-size: 18px;
    font-weight: 700;
  }

  &__call {
    align-self: flex-start;
  }

  &__subtitle {
    font-size: 17px;
    font-weight: 600;
  }

  &__building {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 12px;
  }

  &__change {
    padding: 0;
    border: 0;
    background: none;
    color: var(--color-text-muted);
    font: inherit;
    font-size: 14px;
    text-decoration: underline;
    cursor: pointer;
  }

  &__textarea {
    min-height: 96px;
    padding-block: 12px;
    resize: vertical;
  }

  &__consent {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 14px;

    input {
      flex: none;
      width: 20px;
      height: 20px;
      margin-top: 1px;
      accent-color: var(--color-text);
    }
  }

  &__doc {
    text-decoration: underline;
  }
}

@media (min-width: 1024px) {
  .service__title {
    font-size: 28px;
  }
}
</style>
