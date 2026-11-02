import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { readJson, writeJson } from '~/shared/lib/storage'
import type { Building } from './types'

const STORAGE_KEY = 'sb97-location'

interface SavedLocation {
  building: Building | null
  sourceCode: string | null
  entrance: string
  floor: number | null
  apartment: string
}

// Корпус из QR и квартира покупателя: при следующем заказе вводить заново не нужно
export const useLocationStore = defineStore('location', () => {
  // ── State ──
  const building = ref<Building | null>(null)
  // Код QR, по которому пришёл покупатель, для аналитики по корпусам
  const sourceCode = ref<string | null>(null)
  const entrance = ref('')
  const floor = ref<number | null>(null)
  const apartment = ref('')

  // ── Actions ──
  function setBuilding(value: Building) {
    building.value = value
    sourceCode.value = value.code
  }

  function clearBuilding() {
    building.value = null
  }

  function hydrate() {
    const saved = readJson<Partial<SavedLocation>>(STORAGE_KEY, {})
    building.value = saved.building ?? null
    sourceCode.value = saved.sourceCode ?? null
    entrance.value = saved.entrance ?? ''
    floor.value = saved.floor ?? null
    apartment.value = saved.apartment ?? ''

    watch([building, sourceCode, entrance, floor, apartment], () => {
      writeJson(STORAGE_KEY, {
        building: building.value,
        sourceCode: sourceCode.value,
        entrance: entrance.value,
        floor: floor.value,
        apartment: apartment.value,
      } satisfies SavedLocation)
    })
  }

  return { building, sourceCode, entrance, floor, apartment, setBuilding, clearBuilding, hydrate }
})
