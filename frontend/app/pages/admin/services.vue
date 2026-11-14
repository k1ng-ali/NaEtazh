<script setup lang="ts">
import PhoneInput from '~/shared/ui/PhoneInput.vue'
import { onMounted, ref } from 'vue'
import { useStaffServicesApi } from '~/features/staff/services/api'
import type { ShopServiceAdmin, ShopServicePayload } from '~/features/staff/services/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin'] })
useHead({ title: 'Услуги | Кабинет' })

interface Draft extends ShopServicePayload {
  // Пусто у новой услуги
  id: number | null
  slug: string | null
}

const api = useStaffServicesApi()
const toast = useToast()

const drafts = ref<Draft[]>([])
const generalPhone = ref('')
const isSavingPhone = ref(false)
const savingId = ref<number | 'new' | null>(null)
const loadError = ref('')

const toDraft = (service: ShopServiceAdmin): Draft => ({ ...service })
const emptyDraft = (): Draft => ({
  id: null,
  slug: null,
  name: '',
  summary: null,
  description: null,
  price_text: null,
  phone: null,
  position: (drafts.value.at(-1)?.position ?? 0) + 1,
  is_active: true,
})

async function load() {
  try {
    const [services, contacts] = await Promise.all([api.listServices(), api.getContacts()])
    drafts.value = services.map(toDraft)
    generalPhone.value = contacts.phone ?? ''
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить услуги')
  }
}

// Номер с ошибкой сервер отклоняет с 422, объясняем по-человечески
const saveError = (error: unknown) =>
  (error as { statusCode?: number })?.statusCode === 422
    ? 'Проверьте телефон: нужно 11 цифр, например +7 (345) 250-50-50 или 8 (800) 555-35-35'
    : errorMessage(error)

async function savePhone() {
  isSavingPhone.value = true
  try {
    generalPhone.value = (await api.setContacts({ phone: generalPhone.value || null })).phone ?? ''
    toast.success('Телефон сохранён')
  } catch (error) {
    toast.error(saveError(error))
  } finally {
    isSavingPhone.value = false
  }
}

async function save(index: number) {
  const draft = drafts.value[index]
  if (!draft) return
  const payload: ShopServicePayload = {
    name: draft.name,
    summary: draft.summary || null,
    description: draft.description || null,
    price_text: draft.price_text || null,
    phone: draft.phone || null,
    position: Number(draft.position) || 0,
    is_active: draft.is_active,
  }
  savingId.value = draft.id ?? 'new'
  try {
    const saved = draft.id ? await api.updateService(draft.id, payload) : await api.createService(payload)
    drafts.value[index] = toDraft(saved)
    toast.success(draft.id ? 'Сохранено' : 'Услуга добавлена')
  } catch (error) {
    toast.error(saveError(error))
  } finally {
    savingId.value = null
  }
}

onMounted(load)
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <h1 class="a-title">Услуги</h1>
      <button
        class="a-btn a-btn--ghost"
        type="button"
        :disabled="drafts.some((draft) => draft.id === null)"
        @click="drafts.push(emptyDraft())"
      >
        Добавить услугу
      </button>
    </div>
    <p class="a-muted">
      Список на странице «Услуги» и на главной. Цену пишите как покупателю: «от 1 500 ₽», «350 ₽ за м²». Пустая цена —
      «Цену назовём после звонка». Заявки приходят менеджеру в раздел «Заявки».
    </p>

    <p v-if="loadError" class="a-error" role="alert">{{ loadError }}</p>
    <form v-else class="a-card" @submit.prevent="savePhone">
      <h2 class="a-subtitle">Телефон для звонков</h2>
      <p class="a-muted">
        Кнопка «Позвонить» на странице услуг. Если у услуги указан свой телефон, на её странице будет он. Пусто —
        кнопки нет.
      </p>
      <div class="row">
        <label class="a-field phone">
          <span>Общий телефон</span>
          <PhoneInput v-model="generalPhone" class="a-input" keep-eight placeholder="+7 (345) 250-50-50" />
        </label>
        <button class="a-btn" type="submit" :disabled="isSavingPhone">
          {{ isSavingPhone ? 'Сохраняем…' : 'Сохранить' }}
        </button>
      </div>
    </form>
    <form
      v-for="(draft, index) in drafts"
      :key="draft.id ?? 'new'"
      class="a-card"
      @submit.prevent="save(index)"
    >
      <div class="head">
        <h2 class="a-subtitle">{{ draft.name || 'Новая услуга' }}</h2>
        <NuxtLink v-if="draft.slug && draft.is_active" :to="`/services/${draft.slug}`" target="_blank" class="a-muted">
          Открыть на сайте
        </NuxtLink>
      </div>
      <div class="a-grid a-grid--2">
        <label class="a-field">
          <span>Название</span>
          <input v-model="draft.name" class="a-input" required maxlength="80">
        </label>
        <label class="a-field">
          <span>Цена</span>
          <input v-model="draft.price_text" class="a-input" maxlength="60" placeholder="Цену назовём после звонка">
        </label>
      </div>
      <label class="a-field">
        <span>Свой телефон услуги</span>
        <PhoneInput v-model="draft.phone" class="a-input" keep-eight :placeholder="generalPhone ? `Общий: ${generalPhone}` : 'Общий телефон магазина'" />
      </label>
      <label class="a-field">
        <span>Коротко для карточки</span>
        <input v-model="draft.summary" class="a-input" maxlength="120">
      </label>
      <label class="a-field">
        <span>Описание</span>
        <textarea v-model="draft.description" class="a-textarea" maxlength="2000" />
      </label>
      <div class="row">
        <label class="a-field position">
          <span>Порядок</span>
          <input v-model.number="draft.position" class="a-input" type="number" min="0" max="1000">
        </label>
        <label class="a-check">
          <input v-model="draft.is_active" type="checkbox">
          Показывать на сайте
        </label>
        <button class="a-btn" type="submit" :disabled="savingId === (draft.id ?? 'new')">
          {{ savingId === (draft.id ?? 'new') ? 'Сохраняем…' : 'Сохранить' }}
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped lang="scss">
.head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px 16px;
}

.position {
  width: 110px;
}

.phone {
  flex: 1 1 220px;
  max-width: 320px;
}
</style>
