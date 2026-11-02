<script setup lang="ts">
import { LEGAL_LINKS, LEGAL_UPDATED_AT } from '~/shared/lib/legal'

defineProps<{ title: string }>()
</script>

<template>
  <div class="container legal">
    <article class="card legal__doc">
      <h1 class="legal__title">{{ title }}</h1>
      <p class="muted legal__date">Редакция от {{ LEGAL_UPDATED_AT }}</p>
      <slot />
    </article>
    <nav class="legal__nav" aria-label="Документы">
      <NuxtLink v-for="link in LEGAL_LINKS" :key="link.to" :to="link.to" class="legal__link">
        {{ link.label }}
      </NuxtLink>
    </nav>
  </div>
</template>

<style scoped lang="scss">
.legal {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__doc {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-width: 760px;
    line-height: 1.5;

    :slotted(h2) {
      margin-top: 12px;
      font-size: 18px;
      font-weight: 600;
    }

    :slotted(ul) {
      margin: 0;
      padding-left: 20px;
    }

    :slotted(li + li) {
      margin-top: 4px;
    }

    :slotted(a) {
      text-decoration: underline;
    }
  }

  &__title {
    font-size: 22px;
    font-weight: 700;
    line-height: 1.25;
  }

  &__date {
    font-size: 14px;
  }

  &__nav {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 16px;
  }

  &__link {
    display: inline-flex;
    align-items: center;
    min-height: var(--tap-size);
    color: var(--color-text-muted);
    text-decoration: underline;

    &.router-link-active {
      color: var(--color-text);
      font-weight: 600;
      text-decoration: none;
    }
  }
}

@media (min-width: 1024px) {
  .legal {
    &__doc {
      padding: 32px;
    }

    &__title {
      font-size: 28px;
    }
  }
}
</style>
