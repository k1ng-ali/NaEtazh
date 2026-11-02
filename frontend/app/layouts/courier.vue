<script setup lang="ts">
import '~/assets/scss/admin.scss'
import { useAuthStore } from '~/features/staff/auth/store'
import AdminToasts from '~/features/staff/shared/components/AdminToasts.vue'

const auth = useAuthStore()

async function logout() {
  await auth.logout()
  await navigateTo('/login')
}
</script>

<template>
  <div class="courier">
    <header class="courier__header">
      <NuxtLink to="/courier" class="courier__title">
        Доставки
        <span>{{ auth.user?.name }}</span>
      </NuxtLink>
      <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="logout">Выйти</button>
    </header>
    <main class="courier__main">
      <slot />
    </main>
    <AdminToasts />
  </div>
</template>

<style scoped lang="scss">
// Один столбец и на телефоне, и на компьютере: курьер работает с телефона в машине
.courier {
  min-height: 100vh;
  background: var(--color-bg);

  &__header {
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 60px;
    padding: 0 16px;
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-line);
  }

  &__title {
    display: flex;
    flex-direction: column;
    font-size: 18px;
    font-weight: 700;

    span {
      color: var(--color-text-muted);
      font-size: 13px;
      font-weight: 500;
    }
  }

  &__main {
    width: 100%;
    max-width: 560px;
    margin: 0 auto;
    padding: 16px 16px calc(32px + env(safe-area-inset-bottom));
  }
}
</style>
