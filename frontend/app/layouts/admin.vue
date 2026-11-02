<script setup lang="ts">
import '~/assets/scss/admin.scss'
import { useAuthStore } from '~/features/admin/auth/store'
import AdminToasts from '~/features/admin/shared/components/AdminToasts.vue'

const auth = useAuthStore()

const NAV = [
  { to: '/admin/products', label: 'Товары', icon: 'M4 7l8-4 8 4-8 4-8-4zm0 0v10l8 4m-8-14l8 4m0 10l8-4V7m-8 14V11' },
  { to: '/admin/categories', label: 'Категории', icon: 'M4 5h7v6H4zM13 5h7v6h-7zM4 13h7v6H4zM13 13h7v6h-7z' },
  { to: '/admin/offers', label: 'Партнёр', icon: 'M4 12h12m0 0l-4-4m4 4l-4 4M20 5v14' },
  { to: '/admin/pricing', label: 'Наценка', icon: 'M19 5L5 19M7.5 9a1.5 1.5 0 100-3 1.5 1.5 0 000 3zm9 9a1.5 1.5 0 100-3 1.5 1.5 0 000 3z' },
]

async function logout() {
  await auth.logout()
  await navigateTo('/admin/login')
}
</script>

<template>
  <div class="admin">
    <!-- Десктоп: боковое меню -->
    <aside class="admin__sidebar">
      <NuxtLink to="/admin/products" class="admin__logo">
        СтройБаза97
        <span>Админка</span>
      </NuxtLink>
      <nav class="admin__nav" aria-label="Разделы">
        <NuxtLink v-for="item in NAV" :key="item.to" :to="item.to" class="admin__nav-link">
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
      <NuxtLink to="/admin/products" class="admin__logo">СтройБаза97 <span>Админка</span></NuxtLink>
      <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="logout">Выйти</button>
    </header>

    <main class="admin__main">
      <slot />
    </main>

    <nav class="admin__tabs" aria-label="Разделы">
      <NuxtLink v-for="item in NAV" :key="item.to" :to="item.to" class="admin__tab">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path :d="item.icon" /></svg>
        {{ item.label }}
      </NuxtLink>
    </nav>

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
    grid-template-columns: repeat(4, minmax(0, 1fr));
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
    font-size: 12px;
    font-weight: 500;

    &.router-link-active {
      color: var(--color-text);
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
    &__tabs {
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

      &.router-link-active {
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
