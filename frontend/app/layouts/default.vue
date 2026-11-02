<script setup lang="ts">
import CatalogSearch from '~/features/catalog/components/CatalogSearch.vue'
import { useCartStore } from '~/features/cart/store'
import CookieBanner from '~/features/cookies/components/CookieBanner.vue'
import { useLocationStore } from '~/features/location/store'
import { LEGAL_LINKS, SELLER } from '~/shared/lib/legal'

const cart = useCartStore()
const location = useLocationStore()
const route = useRoute()
</script>

<template>
  <div class="layout">
    <header class="header">
      <div class="container header__inner">
        <NuxtLink to="/" class="header__logo">СтройБаза97</NuxtLink>
        <!-- На десктопе поиск всегда в шапке -->
        <CatalogSearch
          class="header__search"
          :value="typeof route.query.search === 'string' ? route.query.search : ''"
        />
        <nav class="header__nav" aria-label="Основное меню">
          <NuxtLink to="/catalog" class="header__link">Каталог</NuxtLink>
          <NuxtLink to="/cart" class="header__link header__cart">
            Корзина
            <ClientOnly>
              <span v-if="cart.count" class="header__count" :aria-label="`товаров: ${cart.count}`">{{ cart.count }}</span>
            </ClientOnly>
          </NuxtLink>
        </nav>
      </div>
      <ClientOnly>
        <div v-if="location.building" class="header__building">
          <div class="container">
            Доставка в {{ location.building.complex_name }}, {{ location.building.name }}
          </div>
        </div>
      </ClientOnly>
    </header>
    <main class="layout__main">
      <slot />
    </main>
    <footer class="footer">
      <div class="container footer__inner">
        <div class="footer__row">
          <span>{{ SELLER.shopName }}</span>
          <span>Оплата при получении наличными</span>
        </div>
        <nav class="footer__links" aria-label="Документы">
          <NuxtLink v-for="link in LEGAL_LINKS" :key="link.to" :to="link.to" class="footer__link">
            {{ link.label }}
          </NuxtLink>
        </nav>
        <p class="footer__seller">
          {{ SELLER.legalName }}, ОГРН {{ SELLER.ogrn }}, ИНН {{ SELLER.inn }}
        </p>
      </div>
    </footer>
    <ClientOnly>
      <CookieBanner />
    </ClientOnly>
  </div>
</template>

<style scoped lang="scss">
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;

  &__main {
    flex: 1;
    padding-block: 16px 32px;
  }
}

.header {
  position: sticky;
  top: 0;
  z-index: 20;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-line);

  &__inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    min-height: 60px;
  }

  &__logo {
    flex-shrink: 0;
    font-size: 18px;
    font-weight: 700;
  }

  &__search {
    display: none;
  }

  &__nav {
    display: flex;
    gap: 4px;
  }

  &__link {
    display: flex;
    align-items: center;
    gap: 6px;
    min-height: var(--tap-size);
    padding: 0 8px;
    font-weight: 500;

    &.router-link-active {
      font-weight: 700;
    }
  }

  &__count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 22px;
    height: 22px;
    padding: 0 6px;
    border-radius: 11px;
    background: var(--color-text);
    color: var(--color-inverse);
    font-size: 13px;
    font-weight: 700;
  }

  &__building {
    padding-block: 6px;
    background: var(--color-text);
    color: var(--color-inverse);
    font-size: 14px;
  }
}

.footer {
  padding-block: 20px;
  border-top: 1px solid var(--color-line);
  color: var(--color-text-muted);
  font-size: 14px;

  &__inner {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__row,
  &__links {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 0 16px;
  }

  &__links {
    justify-content: flex-start;
  }

  &__link {
    display: inline-flex;
    align-items: center;
    min-height: var(--tap-size);
    text-decoration: underline;
  }

  &__seller {
    font-size: 13px;
  }
}

@media (min-width: 1024px) {
  .header {
    &__inner {
      min-height: 72px;
    }

    &__search {
      display: flex;
      flex: 1;
      max-width: 560px;
    }
  }

  .layout__main {
    padding-block: 24px 48px;
  }
}
</style>
