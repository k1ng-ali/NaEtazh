<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAdminCatalogApi } from '~/features/staff/catalog/api'
import ProductForm from '~/features/staff/catalog/components/ProductForm.vue'
import ProductImages from '~/features/staff/catalog/components/ProductImages.vue'
import ProductStatusBadge from '~/features/staff/catalog/components/ProductStatusBadge.vue'
import ProductStock from '~/features/staff/catalog/components/ProductStock.vue'
import { useAdminCatalogStore } from '~/features/staff/catalog/store'
import type { AdminProduct, ProductPayload, StockPayload } from '~/features/staff/catalog/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'
import { formatPrice, formatQuantity } from '~/shared/lib/format'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin', 'manager'] })

const api = useAdminCatalogApi()
const catalog = useAdminCatalogStore()
const toast = useToast()
const route = useRoute()

const isNew = computed(() => route.params.id === 'new')
const product = ref<AdminProduct | null>(null)
const isLoading = ref(!isNew.value)
const isSaving = ref(false)
const isUploading = ref(false)
const loadError = ref('')

useHead(() => ({ title: `${product.value?.name ?? 'Новый товар'} | Кабинет` }))

async function load() {
  if (isNew.value) return
  try {
    product.value = await api.getProduct(Number(route.params.id))
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить товар')
  } finally {
    isLoading.value = false
  }
}

async function save(payload: ProductPayload) {
  isSaving.value = true
  try {
    if (product.value) {
      product.value = await api.updateProduct(product.value.id, payload)
      toast.success('Сохранено')
    } else {
      const created = await api.createProduct(payload)
      toast.success('Товар создан. Теперь можно добавить фото и остаток')
      await navigateTo(`/manager/products/${created.id}`, { replace: true })
    }
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSaving.value = false
  }
}

async function upload(files: File[]) {
  if (!product.value) return
  isUploading.value = true
  try {
    // По одному: сервер сжимает каждое фото
    for (const file of files) {
      product.value = await api.uploadImage(product.value.id, file)
    }
  } catch (error) {
    toast.error(errorMessage(error, 'Не удалось загрузить фото'))
  } finally {
    isUploading.value = false
  }
}

async function changeImages(images: string[]) {
  if (!product.value) return
  try {
    product.value = await api.updateProduct(product.value.id, { images })
  } catch (error) {
    toast.error(errorMessage(error))
  }
}

async function saveStock(payload: StockPayload) {
  if (!product.value) return
  isSaving.value = true
  try {
    product.value = await api.setStock(product.value.id, payload)
    toast.success('Остаток сохранён')
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSaving.value = false
  }
}

onMounted(() => Promise.all([load(), catalog.loadCategories(), catalog.loadWarehouses()]))
</script>

<template>
  <div class="a-page">
    <NuxtLink to="/manager/products" class="a-muted back">← Все товары</NuxtLink>

    <p v-if="loadError" class="a-error" role="alert">{{ loadError }}</p>
    <p v-else-if="isLoading" class="a-muted">Загружаем…</p>

    <template v-else>
      <div class="a-page-head">
        <h1 class="a-title">{{ product?.name ?? 'Новый товар' }}</h1>
        <ProductStatusBadge v-if="product" :status="product.status" />
      </div>

      <div class="layout">
        <ProductForm
          class="layout__main"
          :product="product"
          :category-options="catalog.categoryOptions"
          :has-offers="Boolean(product?.offers.length)"
          :is-saving="isSaving"
          @submit="save"
        />

        <aside class="layout__side">
          <template v-if="product">
            <ProductImages
              :images="product.images"
              :is-uploading="isUploading"
              @upload="upload"
              @change="changeImages"
            />
            <ProductStock
              :stock="product.stock"
              :warehouses="catalog.warehouses"
              :unit="product.unit"
              :is-saving="isSaving"
              @save="saveStock"
            />
            <section class="a-card">
              <h2 class="a-subtitle">У партнёра</h2>
              <p v-if="!product.offers.length" class="a-muted">
                Не привязан. Привязать можно в разделе «Партнёр».
              </p>
              <div v-for="offer in product.offers" :key="offer.id" class="offer">
                <a v-if="offer.url" :href="offer.url" target="_blank" rel="noopener noreferrer" class="offer__name">
                  {{ offer.name }}
                </a>
                <span v-else class="offer__name">{{ offer.name }}</span>
                <span class="a-muted">
                  {{ offer.supplier_name }} · закупка {{ formatPrice(offer.price) }} · остаток {{ formatQuantity(offer.quantity) }}
                </span>
                <span v-if="!offer.is_active" class="a-badge a-badge--danger">Пропал из выгрузки</span>
              </div>
            </section>
          </template>
          <section v-else class="a-card a-muted">
            Фото, остатки склада и связь с партнёром появятся после сохранения товара.
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

.layout {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__side {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}

.offer {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;

  &__name {
    font-weight: 600;
  }

  a.offer__name:hover {
    text-decoration: underline;
  }
}

/* На десктопе форма слева, фото и остатки справа */
@media (min-width: 1024px) {
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 360px;
    align-items: start;
  }
}

@media (min-width: 1280px) {
  .layout {
    grid-template-columns: minmax(0, 1fr) 400px;
  }
}
</style>
