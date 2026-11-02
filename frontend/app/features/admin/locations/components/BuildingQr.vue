<script setup lang="ts">
import QRCode from 'qrcode'
import { computed, ref, watch } from 'vue'
import type { AdminBuilding } from '../types'

const props = defineProps<{
  building: AdminBuilding
  complexName: string
}>()

const { siteUrl } = useRuntimeConfig().public
const url = computed(() => `${siteUrl}/k/${props.building.code}`)
const image = ref('')

// Крупный PNG с запасом для печати на визитке
watch(
  url,
  async (value) => {
    image.value = await QRCode.toDataURL(value, { width: 1024, margin: 2, errorCorrectionLevel: 'M' })
  },
  { immediate: true },
)

const filename = computed(() => `qr-${props.complexName}-${props.building.name}`.replace(/[^\p{L}\p{N}]+/gu, '-').toLowerCase())
</script>

<template>
  <div class="qr">
    <img v-if="image" :src="image" :alt="`QR-код: ${complexName}, ${building.name}`" class="qr__image">
    <div class="qr__body">
      <span class="qr__url">{{ url }}</span>
      <a v-if="image" :href="image" :download="`${filename}.png`" class="a-btn a-btn--ghost a-btn--small">Скачать PNG</a>
    </div>
  </div>
</template>

<style scoped lang="scss">
.qr {
  display: flex;
  align-items: center;
  gap: 12px;

  &__image {
    flex-shrink: 0;
    width: 88px;
    height: 88px;
    border: 1px solid var(--color-line);
    border-radius: 8px;
  }

  &__body {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    min-width: 0;
  }

  &__url {
    overflow-wrap: anywhere;
    font-size: 13px;
  }
}
</style>
