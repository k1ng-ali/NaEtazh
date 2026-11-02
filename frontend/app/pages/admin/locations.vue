<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useAuthStore } from '~/features/staff/auth/store'
import { useLocationsApi } from '~/features/staff/locations/api'
import BuildingQr from '~/features/staff/locations/components/BuildingQr.vue'
import TariffForm from '~/features/staff/locations/components/TariffForm.vue'
import type { AdminComplex, Tariff, TariffPayload } from '~/features/staff/locations/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin'] })
useHead({ title: 'Дома и доставка | Кабинет' })

const api = useLocationsApi()
const auth = useAuthStore()
const toast = useToast()

const complexes = ref<AdminComplex[]>([])
const tariffs = ref<Tariff[]>([])
const loadError = ref('')
const isSaving = ref(false)
// Комплексы, для которых открыта форма своего тарифа
const customTariffOpen = reactive<Record<number, boolean>>({})

const complexForm = reactive({ name: '', address: '' })
const buildingForms = reactive<Record<number, { name: string; floors: string; lift: string }>>({})

const defaultTariff = computed(() => tariffs.value.find((item) => item.complex_id === null) ?? null)
const tariffOf = (complexId: number) => tariffs.value.find((item) => item.complex_id === complexId) ?? null

function buildingForm(complexId: number) {
  buildingForms[complexId] ??= { name: '', floors: '', lift: '' }
  return buildingForms[complexId]
}

async function load() {
  try {
    ;[complexes.value, tariffs.value] = await Promise.all([api.listComplexes(), api.listTariffs()])
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить дома')
  }
}

async function withSaving(action: () => Promise<void>, success: string) {
  isSaving.value = true
  try {
    await action()
    toast.success(success)
    await load()
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSaving.value = false
  }
}

const addComplex = () =>
  withSaving(async () => {
    await api.createComplex({ name: complexForm.name.trim(), address: complexForm.address.trim() || null })
    Object.assign(complexForm, { name: '', address: '' })
  }, 'Жилой комплекс добавлен')

const addBuilding = (complexId: number) =>
  withSaving(async () => {
    const form = buildingForm(complexId)
    await api.createBuilding(complexId, {
      name: form.name.trim(),
      floors: Number(form.floors) || null,
      cargo_lift_length_mm: Number(form.lift) || null,
    })
    Object.assign(form, { name: '', floors: '', lift: '' })
  }, 'Корпус добавлен, QR-код готов')

const saveTariff = (payload: TariffPayload) => withSaving(async () => void (await api.saveTariff(payload)), 'Тариф сохранён')

const removeTariff = (tariff: Tariff) => {
  if (!confirm('Удалить свой тариф комплекса? Будет действовать общий.')) return
  return withSaving(async () => {
    await api.deleteTariff(tariff.id)
    if (tariff.complex_id) customTariffOpen[tariff.complex_id] = false
  }, 'Тариф удалён')
}

onMounted(load)
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <div>
        <h1 class="a-title">Дома и доставка</h1>
        <p class="a-muted">Корпуса для QR-кодов на визитках и цены доставки с подъёмом</p>
      </div>
    </div>

    <p v-if="loadError" class="a-error" role="alert">{{ loadError }}</p>

    <section class="a-card">
      <h2 class="a-subtitle">Общий тариф</h2>
      <p v-if="!defaultTariff" class="a-error">
        Не задан. Пока его нет, покупатель видит «Стоимость доставки сообщит менеджер».
      </p>
      <TariffForm :complex-id="null" :tariff="defaultTariff" :can-edit="auth.isAdmin" :is-saving="isSaving" @save="saveTariff" />
      <p v-if="!auth.isAdmin" class="a-muted">Тарифы меняет администратор.</p>
    </section>

    <section v-for="complex in complexes" :key="complex.id" class="a-card">
      <div>
        <h2 class="a-subtitle">{{ complex.name }}</h2>
        <p v-if="complex.address" class="a-muted">{{ complex.address }}</p>
      </div>

      <p v-if="!complex.buildings.length" class="a-muted">Корпусов пока нет. Добавьте их, чтобы получить QR-коды.</p>
      <div class="buildings">
        <div v-for="building in complex.buildings" :key="building.id" class="building">
          <div class="building__info">
            <strong>{{ building.name }}</strong>
            <span class="a-muted">
              {{ building.floors ? `${building.floors} этажей` : 'Этажность не указана' }} ·
              {{ building.cargo_lift_length_mm ? `лифт до ${building.cargo_lift_length_mm} мм` : 'лифт не указан' }}
            </span>
          </div>
          <BuildingQr :building="building" :complex-name="complex.name" />
        </div>
      </div>

      <form class="building-form" @submit.prevent="addBuilding(complex.id)">
        <label class="a-field">
          <span class="a-field__label">Корпус</span>
          <input v-model="buildingForm(complex.id).name" class="a-input" required maxlength="60" placeholder="Корпус 3">
        </label>
        <label class="a-field">
          <span class="a-field__label">Этажей</span>
          <input v-model="buildingForm(complex.id).floors" class="a-input" inputmode="numeric" pattern="\d*">
        </label>
        <label class="a-field">
          <span class="a-field__label">Длина в лифте, мм</span>
          <input v-model="buildingForm(complex.id).lift" class="a-input" inputmode="numeric" pattern="\d*">
        </label>
        <button class="a-btn a-btn--ghost" type="submit" :disabled="isSaving">Добавить корпус</button>
      </form>

      <div class="complex-tariff">
        <template v-if="tariffOf(complex.id) || customTariffOpen[complex.id]">
          <div class="complex-tariff__head">
            <h3 class="a-subtitle">Свой тариф комплекса</h3>
            <button
              v-if="tariffOf(complex.id) && auth.isAdmin"
              class="a-btn a-btn--danger a-btn--small"
              type="button"
              @click="removeTariff(tariffOf(complex.id)!)"
            >
              Удалить
            </button>
          </div>
          <TariffForm
            :complex-id="complex.id"
            :tariff="tariffOf(complex.id) ?? defaultTariff"
            :can-edit="auth.isAdmin"
            :is-saving="isSaving"
            @save="saveTariff"
          />
        </template>
        <button
          v-else-if="auth.isAdmin"
          class="a-btn a-btn--ghost a-btn--small"
          type="button"
          @click="customTariffOpen[complex.id] = true"
        >
          Задать свой тариф для комплекса
        </button>
        <p v-else class="a-muted">Действует общий тариф</p>
      </div>
    </section>

    <form class="a-card" @submit.prevent="addComplex">
      <h2 class="a-subtitle">Новый жилой комплекс</h2>
      <div class="a-grid a-grid--2">
        <label class="a-field">
          <span class="a-field__label">Название</span>
          <input v-model="complexForm.name" class="a-input" required maxlength="120" placeholder="ЖК Северный">
        </label>
        <label class="a-field">
          <span class="a-field__label">Адрес</span>
          <input v-model="complexForm.address" class="a-input" maxlength="250" placeholder="ул. Строителей, 12">
        </label>
      </div>
      <button class="a-btn complex-add" type="submit" :disabled="isSaving">Добавить комплекс</button>
    </form>
  </div>
</template>

<style scoped lang="scss">
.buildings {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 12px;
}

.building {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-control);

  &__info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
}

.building-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  align-items: end;

  .a-field:first-child,
  .a-btn {
    grid-column: 1 / -1;
  }
}

.complex-tariff {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
  padding-top: 14px;
  border-top: 1px solid var(--color-line);

  &__head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    width: 100%;
  }
}

.complex-add {
  align-self: flex-start;
}

@media (min-width: 1024px) {
  .buildings {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .building-form {
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) minmax(0, 1fr) auto;

    .a-field:first-child,
    .a-btn {
      grid-column: auto;
    }
  }
}
</style>
