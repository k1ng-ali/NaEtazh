<script setup lang="ts">
import { computed } from 'vue'
import { ORDER_STATUS } from '~/features/checkout/labels'
import type { OrderStatus } from '~/features/checkout/types'

const props = defineProps<{
  status: OrderStatus
}>()

// Новые и проверяемые требуют действия менеджера, поэтому янтарные
const MODIFIER: Record<OrderStatus, string> = {
  new: 'warning',
  checking: 'warning',
  confirmed: '',
  in_delivery: '',
  delivered: 'success',
  canceled: 'danger',
}

const modifier = computed(() => MODIFIER[props.status])
</script>

<template>
  <span class="a-badge" :class="modifier && `a-badge--${modifier}`">{{ ORDER_STATUS[status] }}</span>
</template>
