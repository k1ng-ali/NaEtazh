<script setup lang="ts">
import { LIFTING } from '~/features/checkout/labels'
import type { LiftingType } from '../types'

defineProps<{
  modelValue: LiftingType
  floor: number | null
  maxFloor: number | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: LiftingType): void
  (e: 'update:floor', value: number | null): void
}>()

const OPTIONS: LiftingType[] = ['none', 'lift', 'stairs']

function onFloor(event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  emit('update:floor', value >= 1 ? Math.floor(value) : null)
}
</script>

<template>
  <fieldset class="lifting card">
    <legend class="lifting__title">Подъём в квартиру</legend>
    <label v-for="option in OPTIONS" :key="option" class="lifting__option" :class="{ 'is-active': modelValue === option }">
      <input type="radio" name="lifting" :value="option" :checked="modelValue === option" @change="emit('update:modelValue', option)">
      {{ LIFTING[option] }}
    </label>
    <label class="field lifting__floor">
      <span class="field__label">Этаж</span>
      <input
        class="input"
        type="number"
        inputmode="numeric"
        min="1"
        :max="maxFloor ?? 100"
        :value="floor ?? ''"
        placeholder="Например, 7"
        @change="onFloor"
      >
    </label>
  </fieldset>
</template>

<style scoped lang="scss">
.lifting {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  border: 0;

  &__title {
    float: left;
    width: 100%;
    margin-bottom: 4px;
    padding: 0;
    font-size: 17px;
    font-weight: 600;
  }

  &__option {
    display: flex;
    align-items: center;
    gap: 10px;
    min-height: 48px;
    padding: 0 12px;
    border: 1.5px solid var(--color-line);
    border-radius: var(--radius-control);
    cursor: pointer;

    &.is-active {
      border-color: var(--color-text);
      font-weight: 600;
    }

    input {
      width: 18px;
      height: 18px;
      accent-color: var(--color-text);
    }
  }

  &__floor {
    max-width: 160px;
  }
}
</style>
