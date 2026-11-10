<script setup lang="ts">
import { computed } from 'vue'
import CartLine from '~/features/cart/components/CartLine.vue'
import CartSummary from '~/features/cart/components/CartSummary.vue'
import LiftingPicker from '~/features/cart/components/LiftingPicker.vue'
import { useCartStore } from '~/features/cart/store'
import { useQuoteSync } from '~/features/cart/useQuoteSync'
import { useLocationStore } from '~/features/location/store'

useHead({ title: 'Корзина | Строй База' })

const cart = useCartStore()
const location = useLocationStore()
useQuoteSync()

const lines = computed(() => new Map((cart.quote?.lines ?? []).map((line) => [line.product_id, line])))
const canCheckout = computed(() => Boolean(cart.quote?.can_order) && !cart.isQuoting)
</script>

<template>
  <div class="container cart">
    <h1 class="cart__title">Корзина</h1>

    <div v-if="!cart.items.length" class="card cart__empty">
      <p>В корзине пока пусто</p>
      <NuxtLink to="/catalog" class="btn">Перейти в каталог</NuxtLink>
    </div>

    <div v-else class="cart__layout">
      <div class="cart__main">
        <section class="card cart__lines">
          <CartLine
            v-for="item in cart.items"
            :key="item.product_id"
            :item="item"
            :line="lines.get(item.product_id) ?? null"
            @quantity="cart.setQuantity(item.product_id, $event)"
            @remove="cart.remove(item.product_id)"
          />
        </section>

        <LiftingPicker
          v-model="cart.liftingType"
          :floor="location.floor"
          :max-floor="location.building?.floors ?? null"
          @update:floor="location.floor = $event"
        />
      </div>

      <aside class="cart__side">
        <CartSummary :quote="cart.quote" :is-quoting="cart.isQuoting">
          <p v-if="cart.quoteError" class="error-text" role="alert">{{ cart.quoteError }}</p>
          <p v-else-if="cart.quote && !cart.quote.can_order" class="error-text">
            Уменьшите количество товаров, которых не хватает
          </p>
          <NuxtLink
            to="/checkout"
            class="btn btn--block btn--large"
            :class="{ 'is-disabled': !canCheckout }"
            :aria-disabled="!canCheckout"
            @click="!canCheckout && $event.preventDefault()"
          >
            Оформить заказ
          </NuxtLink>
        </CartSummary>
        <p class="muted cart__address">
          <template v-if="location.building">
            Доставка в {{ location.building.complex_name }}, {{ location.building.name }}
          </template>
          <template v-else>Адрес доставки укажете при оформлении</template>
        </p>
      </aside>
    </div>
  </div>
</template>

<style scoped lang="scss">
.cart {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__title {
    font-size: 22px;
    font-weight: 700;
  }

  &__empty {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  &__layout,
  &__main,
  &__side {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  &__lines {
    padding-block: 0;
  }

  &__address {
    font-size: 14px;
  }
}

.is-disabled {
  opacity: 0.45;
  pointer-events: none;
}

/* Десктоп: товары слева, итог справа и не уезжает */
@media (min-width: 1024px) {
  .cart {
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
