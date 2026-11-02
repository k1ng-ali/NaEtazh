<script setup lang="ts">
import { useToast } from '../toast'

const { toasts } = useToast()
</script>

<template>
  <div class="toasts" aria-live="polite">
    <TransitionGroup name="toast">
      <p v-for="toast in toasts" :key="toast.id" class="toasts__item" :class="`toasts__item--${toast.type}`">
        {{ toast.text }}
      </p>
    </TransitionGroup>
  </div>
</template>

<style scoped lang="scss">
.toasts {
  position: fixed;
  right: 16px;
  bottom: calc(76px + env(safe-area-inset-bottom));
  left: 16px;
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  pointer-events: none;

  &__item {
    max-width: 480px;
    padding: 12px 16px;
    border-radius: var(--radius-control);
    background: var(--color-text);
    color: var(--color-inverse);
    font-size: 15px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.16);

    &--error {
      background: var(--color-danger);
    }
  }
}

@media (min-width: 1024px) {
  .toasts {
    right: 32px;
    bottom: 32px;
    left: auto;
    align-items: flex-end;
  }
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
