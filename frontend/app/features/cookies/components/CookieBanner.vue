<script setup lang="ts">
import { useCookieStore } from '../store'

const cookies = useCookieStore()
</script>

<template>
  <div v-if="cookies.needsChoice" class="cookie-banner" role="region" aria-label="Cookie">
    <div class="container cookie-banner__inner">
      <p class="cookie-banner__text">
        Корзина хранится в вашем браузере. С вашего разрешения мы также используем cookie
        Яндекс Метрики, чтобы улучшать сайт.
        <NuxtLink to="/legal/privacy" class="cookie-banner__link">Подробнее</NuxtLink>
      </p>
      <div class="cookie-banner__actions">
        <button class="btn btn--ghost" type="button" @click="cookies.choose('necessary')">
          Только необходимые
        </button>
        <button class="btn" type="button" @click="cookies.choose('all')">Принять все</button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.cookie-banner {
  position: fixed;
  inset: auto 0 0;
  z-index: 30;
  padding-block: 12px calc(12px + env(safe-area-inset-bottom));
  background: var(--color-surface);
  border-top: 1px solid var(--color-line);
  box-shadow: 0 -4px 16px rgb(0 0 0 / 6%);

  &__inner {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__text {
    font-size: 14px;
  }

  &__link {
    text-decoration: underline;
  }

  &__actions {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
}

@media (min-width: 768px) {
  .cookie-banner {
    &__inner {
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
      gap: 24px;
    }

    &__actions {
      display: flex;
      flex-shrink: 0;
    }
  }
}
</style>
