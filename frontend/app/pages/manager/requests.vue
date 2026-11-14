<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { REQUEST_STATUS, useStaffServicesApi } from '~/features/staff/services/api'
import type { ServiceRequest, ServiceRequestList, ServiceRequestStatus } from '~/features/staff/services/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'
import { formatDateTime } from '~/shared/lib/format'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin', 'manager'] })
useHead({ title: 'Заявки | Кабинет' })

const PAGE_SIZE = 50
const FILTERS: { value: ServiceRequestStatus | ''; label: string }[] = [
  { value: 'new', label: 'Новые' },
  { value: 'in_progress', label: 'В работе' },
  { value: '', label: 'Все' },
]
const BADGE: Record<ServiceRequestStatus, string> = {
  new: 'a-badge--warning',
  in_progress: '',
  done: 'a-badge--success',
  canceled: 'a-badge--danger',
}

const api = useStaffServicesApi()
const toast = useToast()

const list = ref<ServiceRequestList | null>(null)
const filter = ref<ServiceRequestStatus | ''>('new')
const skip = ref(0)
const busyId = ref<number | null>(null)
const errorText = ref('')

const page = computed(() => Math.floor(skip.value / PAGE_SIZE) + 1)
const pages = computed(() => Math.max(1, Math.ceil((list.value?.total ?? 0) / PAGE_SIZE)))
const dateFormat = new Intl.DateTimeFormat('ru-RU', { weekday: 'short', day: 'numeric', month: 'long' })

async function load() {
  errorText.value = ''
  try {
    list.value = await api.listRequests({ status: filter.value || undefined, skip: skip.value, limit: PAGE_SIZE })
  } catch (error) {
    errorText.value = errorMessage(error, 'Не удалось загрузить заявки')
  }
}

async function setStatus(request: ServiceRequest, status: ServiceRequestStatus) {
  busyId.value = request.id
  try {
    const updated = await api.setRequestStatus(request.id, status)
    toast.success(`Заявка № ${request.id}: ${REQUEST_STATUS[status].toLowerCase()}`)
    if (!list.value) return
    // В фильтре по статусу заявка уходит из списка
    const keep = !filter.value || filter.value === status
    list.value = {
      items: keep
        ? list.value.items.map((item) => (item.id === updated.id ? updated : item))
        : list.value.items.filter((item) => item.id !== updated.id),
      total: keep ? list.value.total : list.value.total - 1,
    }
  } catch (error) {
    toast.error(errorMessage(error))
  } finally {
    busyId.value = null
  }
}

watch(filter, () => {
  skip.value = 0
  load()
})
watch(skip, load)
onMounted(load)
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <h1 class="a-title">Заявки на услуги</h1>
    </div>

    <div class="tabs" role="tablist">
      <button
        v-for="tab in FILTERS"
        :key="tab.value"
        class="tabs__item"
        :class="{ 'is-active': filter === tab.value }"
        type="button"
        role="tab"
        :aria-selected="filter === tab.value"
        @click="filter = tab.value"
      >
        {{ tab.label }}
      </button>
    </div>

    <p v-if="errorText" class="a-error" role="alert">{{ errorText }}</p>
    <div v-else-if="list && !list.items.length" class="a-card a-empty">Заявок нет</div>
    <div v-else-if="list" class="list">
      <article v-for="request in list.items" :key="request.id" class="a-card request">
        <div class="request__head">
          <strong>№ {{ request.id }} · {{ request.service_name }}</strong>
          <span class="a-badge" :class="BADGE[request.status]">{{ REQUEST_STATUS[request.status] }}</span>
        </div>
        <p class="a-muted">{{ formatDateTime(request.created_at) }}</p>
        <p>
          {{ request.customer_name }} ·
          <a :href="`tel:${request.customer_phone}`" class="request__phone">{{ request.customer_phone }}</a>
        </p>
        <p>{{ request.address }}</p>
        <p v-if="request.preferred_date">
          Когда удобно: {{ dateFormat.format(new Date(`${request.preferred_date}T00:00:00`)) }}
        </p>
        <p v-if="request.comment" class="request__comment">{{ request.comment }}</p>
        <div class="request__actions">
          <a :href="`tel:${request.customer_phone}`" class="a-btn">Позвонить</a>
          <button
            v-if="request.status === 'new'"
            class="a-btn a-btn--ghost"
            type="button"
            :disabled="busyId === request.id"
            @click="setStatus(request, 'in_progress')"
          >
            В работу
          </button>
          <button
            v-if="request.status === 'new' || request.status === 'in_progress'"
            class="a-btn a-btn--ghost"
            type="button"
            :disabled="busyId === request.id"
            @click="setStatus(request, 'done')"
          >
            Выполнена
          </button>
          <button
            v-if="request.status === 'new' || request.status === 'in_progress'"
            class="a-btn a-btn--ghost"
            type="button"
            :disabled="busyId === request.id"
            @click="setStatus(request, 'canceled')"
          >
            Отменить
          </button>
        </div>
      </article>
    </div>

    <div v-if="pages > 1" class="a-pager">
      <button class="a-btn a-btn--ghost" type="button" :disabled="page <= 1" @click="skip -= PAGE_SIZE">Назад</button>
      <span class="a-muted">Страница {{ page }} из {{ pages }} · {{ list?.total }}</span>
      <button class="a-btn a-btn--ghost" type="button" :disabled="page >= pages" @click="skip += PAGE_SIZE">
        Дальше
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  padding: 4px;
  border-radius: var(--radius-control);
  background: var(--color-line);

  &__item {
    min-height: 36px;
    padding: 0 10px;
    border: 0;
    border-radius: 8px;
    background: transparent;
    color: var(--color-text-muted);
    font: inherit;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;

    &.is-active {
      background: var(--color-surface);
      color: var(--color-text);
    }
  }
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.request {
  gap: 6px;

  &__head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 8px;
  }

  &__phone {
    text-decoration: underline;
  }

  &__comment {
    white-space: pre-line;
    color: var(--color-text-muted);
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 6px;
  }
}

@media (min-width: 1024px) {
  .tabs {
    max-width: 420px;
  }
}
</style>
