<script setup lang="ts">
import { formatPrice, formatQuantity } from '~/shared/lib/format'
import { useMediaUrl } from '~/shared/lib/media'
import type { ProductRow } from '../types'
import ProductStatusBadge from './ProductStatusBadge.vue'

defineProps<{
  items: ProductRow[]
  categoryNames: Map<number, string>
}>()

const mediaUrl = useMediaUrl()

// Откуда товар можно взять прямо сейчас
function source(row: ProductRow) {
  const stock = Number(row.stock_quantity)
  const partner = Number(row.offer_quantity ?? 0)
  if (stock > 0) return { label: `Склад: ${formatQuantity(stock)}`, modifier: 'success' }
  if (partner > 0) return { label: `Партнёр: ${formatQuantity(partner)}`, modifier: '' }
  return { label: 'Нет в наличии', modifier: 'danger' }
}
</script>

<template>
  <!-- Десктоп: таблица -->
  <div class="products a-card">
    <table class="a-table products__table">
      <thead>
        <tr>
          <th />
          <th>Товар</th>
          <th>Категория</th>
          <th class="a-table__num">Цена</th>
          <th class="a-table__num">Закупка</th>
          <th>Наличие</th>
          <th>Статус</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in items" :key="row.id" class="products__row">
          <td class="products__thumb-cell">
            <div class="products__thumb">
              <img v-if="row.image" :src="mediaUrl(row.image)" alt="" loading="lazy">
            </div>
          </td>
          <td>
            <NuxtLink :to="`/admin/products/${row.id}`" class="products__name">{{ row.name }}</NuxtLink>
            <span class="a-muted">{{ row.sku }}</span>
          </td>
          <td class="a-muted">{{ categoryNames.get(row.category_id) }}</td>
          <td class="a-table__num">
            {{ formatPrice(row.price) }}
            <span v-if="!row.is_price_manual" class="a-muted products__auto" title="Цена от партнёра с наценкой">авто</span>
          </td>
          <td class="a-table__num a-muted">{{ row.offer_price ? formatPrice(row.offer_price) : '—' }}</td>
          <td><span class="a-badge" :class="source(row).modifier && `a-badge--${source(row).modifier}`">{{ source(row).label }}</span></td>
          <td><ProductStatusBadge :status="row.status" /></td>
        </tr>
      </tbody>
    </table>

    <!-- Телефон: карточки -->
    <ul class="products__list">
      <li v-for="row in items" :key="row.id">
        <NuxtLink :to="`/admin/products/${row.id}`" class="products__item">
          <div class="products__thumb">
            <img v-if="row.image" :src="mediaUrl(row.image)" alt="" loading="lazy">
          </div>
          <div class="products__body">
            <span class="products__name">{{ row.name }}</span>
            <span class="products__price">
              {{ formatPrice(row.price) }}
              <span class="a-muted">/ {{ row.unit }}</span>
            </span>
            <span class="products__badges">
              <ProductStatusBadge :status="row.status" />
              <span class="a-badge" :class="source(row).modifier && `a-badge--${source(row).modifier}`">{{ source(row).label }}</span>
            </span>
          </div>
        </NuxtLink>
      </li>
    </ul>
  </div>
</template>

<style scoped lang="scss">
.products {
  gap: 0;
  padding: 0;

  &__table {
    display: none;
  }

  &__list {
    margin: 0;
    padding: 0;
    list-style: none;

    li + li {
      border-top: 1px solid var(--color-line);
    }
  }

  &__item {
    display: flex;
    gap: 12px;
    padding: 12px;
  }

  &__thumb {
    display: flex;
    flex-shrink: 0;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    overflow: hidden;
    border-radius: 8px;
    background: var(--color-bg);

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }

  &__body {
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 0;
  }

  &__name {
    display: block;
    font-weight: 600;
  }

  &__price {
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  &__badges {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  &__auto {
    display: block;
    font-size: 12px;
  }
}

@media (min-width: 1024px) {
  .products {
    padding: 4px 8px;

    &__table {
      display: table;
    }

    &__list {
      display: none;
    }

    &__row:hover td {
      background: var(--color-bg);
    }

    &__thumb-cell {
      width: 64px;
    }

    &__thumb {
      width: 44px;
      height: 44px;
    }

    &__name:hover {
      text-decoration: underline;
    }
  }
}
</style>
