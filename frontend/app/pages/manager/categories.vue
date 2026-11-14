<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useAdminCatalogApi } from '~/features/staff/catalog/api'
import { useAdminCatalogStore } from '~/features/staff/catalog/store'
import type { AdminCategory } from '~/features/staff/catalog/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'
import { useMediaUrl } from '~/shared/lib/media'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin', 'manager'] })
useHead({ title: 'Категории | Кабинет' })

const api = useAdminCatalogApi()
const catalog = useAdminCatalogStore()
const toast = useToast()
const mediaUrl = useMediaUrl()

const emptyForm = () => ({ name: '', slug: '', parent_id: '' as number | '', position: '0', is_active: true })
const form = reactive(emptyForm())
// null: добавляем новую категорию
const editingId = ref<number | null>(null)
const isSaving = ref(false)
const isImageBusy = ref(false)
const loadError = ref('')
const editing = computed(() => (editingId.value ? byId.value.get(editingId.value) ?? null : null))

const byId = computed(() => new Map(catalog.categories.map((item) => [item.id, item])))
const rows = computed(() =>
  catalog.categoryOptions.map((option) => ({ ...byId.value.get(option.id)!, label: option.label, depth: option.depth })),
)
// Категорию нельзя вложить в саму себя
const parentOptions = computed(() => catalog.categoryOptions.filter((option) => option.id !== editingId.value))

function edit(category: AdminCategory) {
  editingId.value = category.id
  Object.assign(form, {
    name: category.name,
    slug: category.slug,
    parent_id: category.parent_id ?? '',
    position: String(category.position),
    is_active: category.is_active,
  })
}

function resetForm() {
  editingId.value = null
  Object.assign(form, emptyForm())
}

async function submit() {
  isSaving.value = true
  const payload = {
    name: form.name.trim(),
    slug: form.slug.trim() || null,
    parent_id: form.parent_id === '' ? null : Number(form.parent_id),
    position: Number(form.position) || 0,
    is_active: form.is_active,
  }
  try {
    if (editingId.value) {
      await api.updateCategory(editingId.value, { ...payload, slug: payload.slug ?? undefined })
      toast.success('Категория сохранена')
    } else {
      await api.createCategory(payload)
      toast.success('Категория добавлена')
    }
    resetForm()
    await catalog.loadCategories()
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSaving.value = false
  }
}

async function uploadImage(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !editingId.value) return
  isImageBusy.value = true
  try {
    await api.uploadCategoryImage(editingId.value, file)
    await catalog.loadCategories()
    toast.success('Картинка сохранена')
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isImageBusy.value = false
  }
}

async function removeImage() {
  if (!editingId.value) return
  isImageBusy.value = true
  try {
    await api.deleteCategoryImage(editingId.value)
    await catalog.loadCategories()
    toast.success('Картинка убрана, на главной будет фото товара')
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isImageBusy.value = false
  }
}

async function remove(category: AdminCategory) {
  if (!confirm(`Удалить категорию «${category.name}»?`)) return
  try {
    await api.deleteCategory(category.id)
    if (editingId.value === category.id) resetForm()
    toast.success('Категория удалена')
    await catalog.loadCategories()
  } catch (error) {
    toast.error(errorMessage(error))
  }
}

onMounted(async () => {
  try {
    await catalog.loadCategories()
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить категории')
  }
})
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <h1 class="a-title">Категории</h1>
    </div>

    <div class="layout">
      <section class="a-card layout__list">
        <p v-if="loadError" class="a-error" role="alert">{{ loadError }}</p>
        <p v-else-if="!rows.length" class="a-empty">Категорий пока нет. Добавьте первую справа.</p>
        <ul v-else class="list">
          <li v-for="row in rows" :key="row.id" class="list__item" :class="{ 'is-editing': row.id === editingId }">
            <div class="list__body" :style="{ paddingLeft: `${row.depth * 20}px` }">
              <span class="list__name">
                <img v-if="row.image" class="list__thumb" :src="mediaUrl(row.image)" alt="">
                {{ row.name }}
              </span>
              <span class="a-muted">
                {{ row.product_count }} тов. · /{{ row.slug }}
                <span v-if="!row.is_active" class="a-badge">Скрыта</span>
              </span>
            </div>
            <div class="list__actions">
              <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="edit(row)">Изменить</button>
              <button
                class="a-btn a-btn--danger a-btn--small"
                type="button"
                :disabled="row.product_count > 0"
                :title="row.product_count > 0 ? 'Сначала перенесите товары' : ''"
                @click="remove(row)"
              >
                Удалить
              </button>
            </div>
          </li>
        </ul>
      </section>

      <form class="a-card layout__form" @submit.prevent="submit">
        <h2 class="a-subtitle">{{ editingId ? 'Изменить категорию' : 'Новая категория' }}</h2>
        <label class="a-field">
          <span class="a-field__label">Название</span>
          <input v-model="form.name" class="a-input" required maxlength="120" placeholder="Штукатурка">
        </label>
        <label class="a-field">
          <span class="a-field__label">Вложить в</span>
          <select v-model="form.parent_id" class="a-select">
            <option value="">Верхний уровень</option>
            <option v-for="option in parentOptions" :key="option.id" :value="option.id">{{ option.label }}</option>
          </select>
        </label>
        <div class="a-grid a-grid--2">
          <label class="a-field">
            <span class="a-field__label">Адрес</span>
            <input v-model="form.slug" class="a-input" maxlength="80" pattern="[a-z0-9\-]*" placeholder="Из названия">
          </label>
          <label class="a-field">
            <span class="a-field__label">Порядок</span>
            <input v-model="form.position" class="a-input" inputmode="numeric" pattern="-?\d+">
          </label>
        </div>
        <label class="a-check">
          <input v-model="form.is_active" type="checkbox">
          Показывать на витрине
        </label>
        <div v-if="editing && editing.parent_id === null" class="image">
          <span class="a-field__label">Картинка на главной</span>
          <img v-if="editing.image" class="image__preview" :src="mediaUrl(editing.image)" alt="">
          <p class="a-muted">
            {{ editing.image
              ? 'Своя картинка вместо фото товара.'
              : 'Сейчас на главной фото самого ходового товара раздела. Можно загрузить свою иллюстрацию.' }}
            JPEG, PNG или WebP до 10 МБ, лучше на белом или прозрачном фоне.
          </p>
          <div class="layout__buttons">
            <label class="a-btn a-btn--ghost a-btn--small" :class="{ 'is-disabled': isImageBusy }">
              {{ editing.image ? 'Заменить' : 'Загрузить' }}
              <input class="image__input" type="file" accept="image/jpeg,image/png,image/webp" :disabled="isImageBusy" @change="uploadImage">
            </label>
            <button
              v-if="editing.image"
              class="a-btn a-btn--ghost a-btn--small"
              type="button"
              :disabled="isImageBusy"
              @click="removeImage"
            >
              Убрать
            </button>
          </div>
        </div>
        <div class="layout__buttons">
          <button class="a-btn" type="submit" :disabled="isSaving">
            {{ editingId ? 'Сохранить' : 'Добавить' }}
          </button>
          <button v-if="editingId" class="a-btn a-btn--ghost" type="button" @click="resetForm">Отмена</button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped lang="scss">
.layout {
  display: flex;
  flex-direction: column-reverse;
  gap: 16px;

  &__list {
    padding: 4px 0;
  }

  &__buttons {
    display: flex;
    gap: 8px;
  }
}

.list {
  margin: 0;
  padding: 0;
  list-style: none;

  &__item {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 12px;
    padding: 12px 16px;

    & + & {
      border-top: 1px solid var(--color-line);
    }

    &.is-editing {
      background: var(--color-bg);
    }
  }

  &__body {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  &__name {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
  }

  &__thumb {
    width: 28px;
    height: 28px;
    object-fit: contain;
    border-radius: 6px;
    background: var(--color-surface);
  }

  &__actions {
    display: flex;
    gap: 6px;
  }
}

.image {
  display: flex;
  flex-direction: column;
  gap: 8px;

  &__preview {
    width: 120px;
    height: 90px;
    object-fit: contain;
    border: 1px solid var(--color-line);
    border-radius: var(--radius-control);
    background: var(--color-surface);
  }

  &__input {
    position: absolute;
    width: 1px;
    height: 1px;
    opacity: 0;
  }

  .is-disabled {
    opacity: 0.5;
    pointer-events: none;
  }
}

/* На десктопе форма справа и не уезжает при прокрутке длинного списка */
@media (min-width: 1024px) {
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 380px;
    align-items: start;

    &__form {
      position: sticky;
      top: 32px;
    }
  }
}
</style>
