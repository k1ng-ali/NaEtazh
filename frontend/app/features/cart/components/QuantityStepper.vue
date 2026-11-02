<script setup lang="ts">
const props = defineProps<{
  modelValue: number
  unit?: string
  min?: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void
}>()

const MAX = 9999

function set(value: number) {
  const min = props.min ?? 1
  emit('update:modelValue', Math.min(Math.max(Math.floor(value) || min, min), MAX))
}
</script>

<template>
  <div class="stepper">
    <button class="stepper__button" type="button" aria-label="Меньше" @click="set(modelValue - 1)">−</button>
    <input
      class="stepper__input"
      :value="modelValue"
      inputmode="numeric"
      :aria-label="`Количество${unit ? `, ${unit}` : ''}`"
      @change="set(Number(($event.target as HTMLInputElement).value))"
    >
    <button class="stepper__button" type="button" aria-label="Больше" @click="set(modelValue + 1)">+</button>
  </div>
</template>

<style scoped lang="scss">
.stepper {
  display: inline-flex;
  align-items: center;
  border: 1.5px solid var(--color-line);
  border-radius: var(--radius-control);
  background: var(--color-surface);

  &__button {
    width: var(--tap-size);
    height: var(--tap-size);
    border: 0;
    background: transparent;
    color: var(--color-text);
    font-size: 20px;
    cursor: pointer;
  }

  &__input {
    width: 52px;
    height: var(--tap-size);
    border: 0;
    background: transparent;
    font-weight: 600;
    text-align: center;
    font-variant-numeric: tabular-nums;

    &:focus {
      outline: 0;
    }
  }
}
</style>
