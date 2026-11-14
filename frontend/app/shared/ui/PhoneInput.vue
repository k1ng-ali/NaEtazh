<script setup lang="ts">
import { caretAfterDigits, formatPhone, onlyDigits, phoneDigits } from '~/shared/lib/phone'

// Поле телефона с автоформатом: «9» → «+7 (9», «8 912» → «+7 (912», вставка любого вида тоже.
// Атрибуты (class, required, placeholder) уходят на сам input
const props = withDefaults(defineProps<{ modelValue: string | null; keepEight?: boolean }>(), {
  keepEight: false,
})
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const options = () => ({ keepEight: props.keepEight })

function onInput(event: Event) {
  const input = event.target as HTMLInputElement
  const inputType = (event as InputEvent).inputType ?? ''
  let raw = input.value
  const caret = input.selectionStart ?? raw.length
  const atEnd = caret >= raw.length
  let digitsBefore = onlyDigits(raw.slice(0, caret)).length

  // Стёрли скобку, пробел или дефис: цифры не изменились, поэтому стираем цифру перед ними
  const previous = formatPhone(props.modelValue ?? '', options())
  if (
    inputType === 'deleteContentBackward' &&
    digitsBefore > 0 &&
    onlyDigits(raw).length === onlyDigits(previous).length
  ) {
    const digits = onlyDigits(raw)
    raw = digits.slice(0, digitsBefore - 1) + digits.slice(digitsBefore)
    digitsBefore -= 1
  }

  // Подставленная впереди семёрка сдвигает курсор на одну цифру
  const shift = phoneDigits(raw, options()).length - Math.min(onlyDigits(raw).length, 11)
  const formatted = formatPhone(raw, options())
  input.value = formatted
  emit('update:modelValue', formatted)

  const position = atEnd ? formatted.length : caretAfterDigits(formatted, digitsBefore + Math.max(shift, 0))
  input.setSelectionRange(position, position)
}
</script>

<template>
  <input
    :value="formatPhone(modelValue ?? '', { keepEight })"
    type="tel"
    inputmode="tel"
    autocomplete="tel"
    maxlength="18"
    @input="onInput"
  >
</template>
