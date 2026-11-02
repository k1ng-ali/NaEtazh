<script setup lang="ts">
import { ref } from 'vue'
import { useMediaUrl } from '~/shared/lib/media'

const props = defineProps<{
  images: string[]
  isUploading: boolean
}>()

const emit = defineEmits<{
  (e: 'upload', files: File[]): void
  (e: 'change', images: string[]): void
}>()

const MAX_IMAGES = 10
const mediaUrl = useMediaUrl()
const input = ref<HTMLInputElement | null>(null)

function onSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const files = Array.from(target.files ?? []).slice(0, MAX_IMAGES - props.images.length)
  if (files.length) emit('upload', files)
  target.value = ''
}

function makeMain(url: string) {
  emit('change', [url, ...props.images.filter((item) => item !== url)])
}

function remove(url: string) {
  if (confirm('Удалить фото?')) emit('change', props.images.filter((item) => item !== url))
}
</script>

<template>
  <section class="a-card">
    <div class="images__head">
      <h2 class="a-subtitle">Фото</h2>
      <span class="a-muted">{{ images.length }} из {{ MAX_IMAGES }}</span>
    </div>

    <div class="images__grid">
      <figure v-for="(url, index) in images" :key="url" class="images__item">
        <img :src="mediaUrl(url)" alt="">
        <span v-if="index === 0" class="a-badge images__main">Главное</span>
        <figcaption class="images__actions">
          <button v-if="index > 0" class="a-btn a-btn--ghost a-btn--small" type="button" @click="makeMain(url)">
            Главным
          </button>
          <button class="a-btn a-btn--danger a-btn--small" type="button" aria-label="Удалить фото" @click="remove(url)">
            ✕
          </button>
        </figcaption>
      </figure>

      <button
        v-if="images.length < MAX_IMAGES"
        class="images__add"
        type="button"
        :disabled="isUploading"
        @click="input?.click()"
      >
        {{ isUploading ? 'Загружаем…' : '+ Добавить фото' }}
      </button>
    </div>
    <p class="a-field__hint">JPG, PNG или WebP до 10 МБ. Сожмём сами, первое фото видно в каталоге.</p>
    <input ref="input" type="file" accept="image/jpeg,image/png,image/webp" multiple hidden @change="onSelect">
  </section>
</template>

<style scoped lang="scss">
.images {
  &__head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  &__item {
    position: relative;
    margin: 0;
    aspect-ratio: 1;
    overflow: hidden;
    border: 1px solid var(--color-line);
    border-radius: var(--radius-control);
    background: var(--color-bg);

    img {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
  }

  &__main {
    position: absolute;
    top: 6px;
    left: 6px;
    background: var(--color-text);
    color: var(--color-inverse);
  }

  &__actions {
    position: absolute;
    right: 6px;
    bottom: 6px;
    display: flex;
    gap: 4px;
  }

  &__add {
    aspect-ratio: 1;
    border: 1.5px dashed var(--color-line);
    border-radius: var(--radius-control);
    background: var(--color-surface);
    color: var(--color-text-muted);
    font: inherit;
    font-weight: 600;
    cursor: pointer;

    &:hover:not(:disabled) {
      border-color: var(--color-text);
      color: var(--color-text);
    }
  }
}

@media (min-width: 640px) and (max-width: 1023px) {
  .images__grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
