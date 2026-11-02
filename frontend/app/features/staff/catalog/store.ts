import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { useAdminCatalogApi } from './api'
import type { AdminCategory, Warehouse } from './types'

// Справочники, которые нужны почти на каждом экране админки
export const useAdminCatalogStore = defineStore('admin-catalog', () => {
  const api = useAdminCatalogApi()

  // ── State ──
  const categories = ref<AdminCategory[]>([])
  const warehouses = ref<Warehouse[]>([])
  const isLoading = ref(false)

  // ── Getters ──
  const categoryNames = computed(() => new Map(categories.value.map((item) => [item.id, item.name])))

  // Плоский список с отступом для вложенных категорий
  const categoryOptions = computed(() => {
    const children = new Map<number | null, AdminCategory[]>()
    for (const item of categories.value) {
      children.set(item.parent_id, [...(children.get(item.parent_id) ?? []), item])
    }
    const result: { id: number; label: string; depth: number }[] = []
    const walk = (parentId: number | null, depth: number) => {
      for (const item of children.get(parentId) ?? []) {
        result.push({ id: item.id, label: `${'— '.repeat(depth)}${item.name}`, depth })
        walk(item.id, depth + 1)
      }
    }
    walk(null, 0)
    return result
  })

  // ── Actions ──
  async function loadCategories() {
    isLoading.value = true
    try {
      categories.value = await api.listCategories()
    } finally {
      isLoading.value = false
    }
  }

  async function loadWarehouses() {
    if (!warehouses.value.length) warehouses.value = await api.listWarehouses()
  }

  return { categories, warehouses, isLoading, categoryNames, categoryOptions, loadCategories, loadWarehouses }
})
