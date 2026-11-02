<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useAdminCatalogStore } from '~/features/admin/catalog/store'
import type { ProductRow } from '~/features/admin/catalog/types'
import { useOffersApi } from '~/features/admin/offers/api'
import OfferItem from '~/features/admin/offers/components/OfferItem.vue'
import type { Offer, OfferList, OfferMatch, Supplier } from '~/features/admin/offers/types'
import { errorMessage } from '~/features/admin/shared/errors'
import { useToast } from '~/features/admin/shared/toast'
import { formatDateTime } from '~/shared/lib/format'

definePageMeta({ layout: 'admin', middleware: 'admin' })
useHead({ title: 'Партнёр | Админка' })

const PAGE_SIZE = 50
const TABS: { value: OfferMatch; label: string }[] = [
  { value: 'unmatched', label: 'Не привязаны' },
  { value: 'matched', label: 'Привязаны' },
  { value: 'all', label: 'Все' },
]

const api = useOffersApi()
const catalog = useAdminCatalogStore()
const toast = useToast()

const supplier = ref<Supplier | null>(null)
const offers = ref<OfferList | null>(null)
const match = ref<OfferMatch>('unmatched')
const search = ref('')
const inStock = ref(true)
const skip = ref(0)
const isSyncing = ref(false)
const busyOfferId = ref<number | null>(null)
const errorText = ref('')

const page = computed(() => Math.floor(skip.value / PAGE_SIZE) + 1)
const pages = computed(() => Math.max(1, Math.ceil((offers.value?.total ?? 0) / PAGE_SIZE)))

async function loadSupplier() {
  // Пока партнёр один, берём первого
  supplier.value = (await api.listSuppliers())[0] ?? null
}

async function loadOffers() {
  if (!supplier.value) return
  errorText.value = ''
  try {
    offers.value = await api.listOffers({
      supplier_id: supplier.value.id,
      match: match.value,
      search: search.value.trim() || undefined,
      in_stock: inStock.value || undefined,
      skip: skip.value,
      limit: PAGE_SIZE,
    })
  } catch (error) {
    errorText.value = errorMessage(error, 'Не удалось загрузить предложения')
  }
}

async function sync() {
  if (!supplier.value) return
  isSyncing.value = true
  try {
    const result = await api.syncSupplier(supplier.value.id)
    supplier.value = result.supplier
    if (result.ok) {
      toast.success('Выгрузка обновлена')
      await loadOffers()
    } else {
      toast.error(result.error ?? 'Не удалось обновить выгрузку')
    }
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    isSyncing.value = false
  }
}

function replaceOffer(updated: Offer) {
  if (!offers.value) return
  // В режиме фильтра предложение уходит из списка после привязки или отвязки
  const keep = match.value === 'all' || (match.value === 'matched') === (updated.product_id !== null)
  offers.value = {
    items: keep
      ? offers.value.items.map((item) => (item.id === updated.id ? updated : item))
      : offers.value.items.filter((item) => item.id !== updated.id),
    total: keep ? offers.value.total : offers.value.total - 1,
  }
}

async function withOffer(offerId: number, action: () => Promise<void>) {
  busyOfferId.value = offerId
  try {
    await action()
    await loadSupplier()
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    busyOfferId.value = null
  }
}

const createProduct = (offer: Offer, categoryId: number) =>
  withOffer(offer.id, async () => {
    const result = await api.createProduct(offer.id, categoryId)
    replaceOffer(result.offer)
    toast.success('Черновик товара создан')
  })

const linkOffer = (offer: Offer, product: ProductRow) =>
  withOffer(offer.id, async () => {
    replaceOffer(await api.linkOffer(offer.id, product.id))
    toast.success(`Привязано к «${product.name}»`)
  })

const unlinkOffer = (offer: Offer) =>
  withOffer(offer.id, async () => {
    replaceOffer(await api.unlinkOffer(offer.id))
    toast.success('Отвязано')
  })

let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    skip.value = 0
    loadOffers()
  }, 300)
})
watch([match, inStock], () => {
  skip.value = 0
  loadOffers()
})
watch(skip, loadOffers)

onMounted(async () => {
  try {
    await Promise.all([loadSupplier(), catalog.loadCategories()])
    await loadOffers()
  } catch (error) {
    errorText.value = errorMessage(error, 'Не удалось загрузить данные партнёра')
  }
})
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <h1 class="a-title">Партнёр</h1>
    </div>

    <section v-if="supplier" class="a-card sync">
      <div class="sync__info">
        <h2 class="a-subtitle">{{ supplier.name }}</h2>
        <p class="a-muted">
          <template v-if="supplier.last_synced_at">
            Обновлено {{ formatDateTime(supplier.last_synced_at) }} ·
            {{ supplier.offers_active }} товаров, не привязано {{ supplier.offers_unmatched }}
          </template>
          <template v-else>Выгрузка ещё не загружалась</template>
        </p>
        <p v-if="supplier.last_sync_error" class="a-error" role="alert">
          Последнее обновление не прошло: {{ supplier.last_sync_error }}. Цены и остатки остались прежними.
        </p>
      </div>
      <button class="a-btn" type="button" :disabled="isSyncing" @click="sync">
        {{ isSyncing ? 'Загружаем выгрузку…' : 'Обновить выгрузку' }}
      </button>
    </section>

    <div class="filters">
      <div class="tabs" role="tablist">
        <button
          v-for="tab in TABS"
          :key="tab.value"
          class="tabs__item"
          :class="{ 'is-active': match === tab.value }"
          type="button"
          role="tab"
          :aria-selected="match === tab.value"
          @click="match = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
      <input v-model="search" class="a-input" type="search" placeholder="Название, бренд, категория" aria-label="Поиск">
      <label class="a-check">
        <input v-model="inStock" type="checkbox">
        Только в наличии
      </label>
    </div>

    <p class="a-muted">
      Цену и остаток берём из выгрузки. Перед заказом менеджер подтверждает наличие у партнёра.
    </p>

    <p v-if="errorText" class="a-error" role="alert">{{ errorText }}</p>
    <div v-else-if="offers && !offers.items.length" class="a-card a-empty">
      {{ supplier?.last_synced_at ? 'Ничего не нашли' : 'Нажмите «Обновить выгрузку», чтобы загрузить товары партнёра' }}
    </div>
    <div v-else-if="offers" class="a-card list">
      <OfferItem
        v-for="offer in offers.items"
        :key="offer.id"
        :offer="offer"
        :category-options="catalog.categoryOptions"
        :is-busy="busyOfferId === offer.id"
        @create="createProduct(offer, $event)"
        @link="linkOffer(offer, $event)"
        @unlink="unlinkOffer(offer)"
      />
    </div>

    <div v-if="pages > 1" class="a-pager">
      <button class="a-btn a-btn--ghost" type="button" :disabled="page <= 1" @click="skip -= PAGE_SIZE">Назад</button>
      <span class="a-muted">Страница {{ page }} из {{ pages }} · {{ offers?.total }}</span>
      <button class="a-btn a-btn--ghost" type="button" :disabled="page >= pages" @click="skip += PAGE_SIZE">
        Дальше
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.sync {
  &__info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
}

.filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 8px;
}

.tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 4px;
  border-radius: var(--radius-control);
  background: var(--color-line);

  &__item {
    min-height: 36px;
    padding: 0 10px;
    border: 0;
    border-radius: 8px;
    background: transparent;
    color: var(--color-text-muted);
    font: inherit;
    font-size: 14px;
    font-weight: 600;
    white-space: nowrap;
    cursor: pointer;

    &.is-active {
      background: var(--color-surface);
      color: var(--color-text);
    }
  }
}

.list {
  gap: 0;
  padding: 0;

  > * + * {
    border-top: 1px solid var(--color-line);
  }
}

@media (min-width: 1024px) {
  .sync {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .filters {
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
  }
}
</style>
