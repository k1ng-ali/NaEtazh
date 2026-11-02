<script setup lang="ts">
import '~/assets/scss/admin.scss'
import { computed, ref, watch } from 'vue'
import { HOME_BY_ROLE, ROLE_LABEL } from '~/features/staff/auth/roles'
import { useAuthStore } from '~/features/staff/auth/store'
import AdminToasts from '~/features/staff/shared/components/AdminToasts.vue'

const auth = useAuthStore()
const route = useRoute()

interface NavItem {
  to: string
  label: string
  icon: string
  // false — на телефоне пункт в меню «Ещё»: внизу помещается пять вкладок
  mobile: boolean
  // Подсвечивать только на самой странице, а не на вложенных
  exact?: boolean
}

const ICONS = {
  dashboard: 'M4 19V9m6 10V5m6 14v-7m4 7H3',
  orders: 'M6 4h12l1 16H5L6 4zm3 4a3 3 0 006 0',
  products: 'M4 7l8-4 8 4-8 4-8-4zm0 0v10l8 4m-8-14l8 4m0 10l8-4V7m-8 14V11',
  categories: 'M4 5h7v6H4zM13 5h7v6h-7zM4 13h7v6H4zM13 13h7v6h-7z',
  offers: 'M4 12h12m0 0l-4-4m4 4l-4 4M20 5v14',
  pricing: 'M19 5L5 19M7.5 9a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm9 9a1.5 1.5 0 100-3 1.5 1.5 0 000 3z',
  locations: 'M4 20V9l8-5 8 5v11h-5v-6H9v6H4z',
  users: 'M16 19v-1a4 4 0 00-8 0v1m4-8a3 3 0 100-6 3 3 0 000 6zm6 8v-1a3 3 0 00-2-2.8M18 5.2a3 3 0 010 5.6',
}

const MANAGER_NAV: NavItem[] = [
  { to: '/manager/orders', label: 'Заказы', icon: ICONS.orders, mobile: true },
  { to: '/manager/products', label: 'Товары', icon: ICONS.products, mobile: true },
  { to: '/manager/offers', label: 'Партнёр', icon: ICONS.offers, mobile: true },
  { to: '/manager/categories', label: 'Категории', icon: ICONS.categories, mobile: true },
]

// Владелец видит свои разделы и всю работу менеджера
const ADMIN_NAV: NavItem[] = [
  { to: '/admin', label: 'Сводка', icon: ICONS.dashboard, mobile: true, exact: true },
  { to: '/manager/orders', label: 'Заказы', icon: ICONS.orders, mobile: true },
  { to: '/manager/products', label: 'Товары', icon: ICONS.products, mobile: true },
  { to: '/admin/locations', label: 'Дома', icon: ICONS.locations, mobile: true },
  { to: '/manager/offers', label: 'Партнёр', icon: ICONS.offers, mobile: false },
  { to: '/manager/categories', label: 'Категории', icon: ICONS.categories, mobile: false },
  { to: '/admin/pricing', label: 'Наценка', icon: ICONS.pricing, mobile: false },
  { to: '/admin/users', label: 'Сотрудники', icon: ICONS.users, mobile: false },
]

const nav = computed(() => (auth.user?.role === 'admin' ? ADMIN_NAV : MANAGER_NAV))
const mobileNav = computed(() => nav.value.filter((item) => item.mobile))
const moreNav = computed(() => nav.value.filter((item) => !item.mobile))
const home = computed(() => (auth.user ? HOME_BY_ROLE[auth.user.role] : '/login'))
const roleLabel = computed(() => (auth.user ? ROLE_LABEL[auth.user.role] : ''))

const isActive = (item: NavItem) =>
  route.path === item.to || (!item.exact && route.path.startsWith(`${item.to}/`))

const isMoreOpen = ref(false)
watch(
  () => route.path,
  () => {
    isMoreOpen.value = false
  },
)

async function logout() {
  await auth.logout()
  await navigateTo('/login')
}
</script>

<template>
  <div class="admin">
    <!-- Десктоп: боковое меню -->
    <aside class="admin__sidebar">
      <NuxtLink :to="home" class="admin__logo">
        СтройБаза97
        <span>{{ roleLabel }}</span>
      </NuxtLink>
      <nav class="admin__nav" aria-label="Разделы">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="admin__nav-link"
          :class="{ 'is-active': isActive(item) }"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true"><path :d="item.icon" /></svg>
          {{ item.label }}
        </NuxtLink>
      </nav>
      <div class="admin__user">
        <span class="admin__user-name">{{ auth.user?.name }}</span>
        <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="logout">Выйти</button>
      </div>
    </aside>

    <!-- Телефон и планшет: шапка сверху, разделы снизу -->
    <header class="admin__topbar">
      <NuxtLink :to="home" class="admin__logo">СтройБаза97 <span>{{ roleLabel }}</span></NuxtLink>
      <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="logout">Выйти</button>
    </header>

    <main class="admin__main">
      <slot />
    </main>

    <nav
      class="admin__tabs"
      aria-label="Разделы"
      :style="{ gridTemplateColumns: `repeat(${mobileNav.length + (moreNav.length ? 1 : 0)}, minmax(0, 1fr))` }"
    >
      <NuxtLink
        v-for="item in mobileNav"
        :key="item.to"
        :to="item.to"
        class="admin__tab"
        :class="{ 'is-active': isActive(item) }"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path :d="item.icon" /></svg>
        {{ item.label }}
      </NuxtLink>
      <button
        v-if="moreNav.length"
        class="admin__tab"
        :class="{ 'is-active': moreNav.some(isActive) }"
        type="button"
        :aria-expanded="isMoreOpen"
        @click="isMoreOpen = !isMoreOpen"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h.01M12 12h.01M19 12h.01" /></svg>
        Ещё
      </button>
    </nav>
    <div v-if="isMoreOpen" class="admin__more">
      <NuxtLink
        v-for="item in moreNav"
        :key="item.to"
        :to="item.to"
        class="admin__more-link"
        :class="{ 'is-active': isActive(item) }"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path :d="item.icon" /></svg>
        {{ item.label }}
      </NuxtLink>
    </div>

    <AdminToasts />
  </div>
</template>

<style scoped lang="scss">
.admin {
  min-height: 100vh;
  background: var(--color-bg);

  &__logo {
    display: flex;
    align-items: baseline;
    gap: 8px;
    font-size: 17px;
    font-weight: 700;

    span {
      color: var(--color-text-muted);
      font-size: 13px;
      font-weight: 500;
    }
  }

  &__sidebar {
    display: none;
  }

  &__topbar {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 56px;
    padding: 0 16px;
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-line);
  }

  &__main {
    width: 100%;
    max-width: 1280px;
    margin: 0 auto;
    // Место под нижнее меню
    padding: 16px 16px calc(88px + env(safe-area-inset-bottom));
  }

  &__tabs {
    position: fixed;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 10;
    display: grid;

    padding-bottom: env(safe-area-inset-bottom);
    background: var(--color-surface);
    border-top: 1px solid var(--color-line);
  }

  &__tab {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    min-height: 60px;
    color: var(--color-text-muted);
    padding: 0;
    border: 0;
    background: transparent;
    font: inherit;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;

    &.is-active {
      color: var(--color-text);
      font-weight: 700;
    }
  }

  &__more {
    position: fixed;
    right: 8px;
    bottom: calc(68px + env(safe-area-inset-bottom));
    z-index: 11;
    display: flex;
    flex-direction: column;
    min-width: 200px;
    padding: 6px;
    border: 1px solid var(--color-line);
    border-radius: var(--radius-card);
    background: var(--color-surface);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.16);
  }

  &__more-link {
    display: flex;
    align-items: center;
    gap: 12px;
    min-height: var(--tap-size);
    padding: 0 12px;
    border-radius: var(--radius-control);
    font-weight: 500;

    &.is-active {
      background: var(--color-bg);
      font-weight: 700;
    }
  }

  svg {
    width: 22px;
    height: 22px;
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 1.8;
  }
}

/* ── Десктоп ─────────────────────────────────────────────────────────── */

@media (min-width: 1024px) {
  .admin {
    display: grid;
    grid-template-columns: 240px minmax(0, 1fr);

    &__topbar,
    &__tabs,
    &__more {
      display: none;
    }

    &__sidebar {
      position: sticky;
      top: 0;
      display: flex;
      flex-direction: column;
      gap: 24px;
      height: 100vh;
      padding: 20px 14px;
      background: var(--color-surface);
      border-right: 1px solid var(--color-line);

      .admin__logo {
        flex-direction: column;
        gap: 2px;
        padding: 0 10px;
      }
    }

    &__nav {
      display: flex;
      flex: 1;
      flex-direction: column;
      gap: 4px;
    }

    &__nav-link {
      display: flex;
      align-items: center;
      gap: 12px;
      min-height: var(--tap-size);
      padding: 0 10px;
      border-radius: var(--radius-control);
      color: var(--color-text-muted);
      font-weight: 500;

      &:hover {
        background: var(--color-bg);
        color: var(--color-text);
      }

      &.is-active {
        background: var(--color-text);
        color: var(--color-inverse);
      }
    }

    &__user {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 12px 10px 0;
      border-top: 1px solid var(--color-line);
    }

    &__user-name {
      overflow: hidden;
      font-size: 14px;
      font-weight: 600;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    &__main {
      padding: 32px 40px 48px;
    }
  }
}
</style>
