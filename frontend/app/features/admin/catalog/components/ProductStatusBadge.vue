<script setup lang="ts">
import { computed } from 'vue'
import type { ProductStatus } from '../types'

const props = defineProps<{
  status: ProductStatus
}>()

const STATUS = {
  published: { label: 'На витрине', modifier: 'success' },
  draft: { label: 'Черновик', modifier: 'warning' },
  archived: { label: 'В архиве', modifier: '' },
} as const

const view = computed(() => STATUS[props.status])
</script>

<template>
  <span class="a-badge" :class="view.modifier && `a-badge--${view.modifier}`">{{ view.label }}</span>
</template>
