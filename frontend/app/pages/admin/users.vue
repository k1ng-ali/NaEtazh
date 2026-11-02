<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ROLE_LABEL } from '~/features/staff/auth/roles'
import { useAuthStore } from '~/features/staff/auth/store'
import type { UserRole } from '~/features/staff/auth/types'
import { errorMessage } from '~/features/staff/shared/errors'
import { useToast } from '~/features/staff/shared/toast'
import { useUsersApi } from '~/features/staff/users/api'
import type { StaffUser } from '~/features/staff/users/types'
import { formatDateTime } from '~/shared/lib/format'

definePageMeta({ layout: 'staff', middleware: 'staff', roles: ['admin'] })
useHead({ title: 'Сотрудники | Кабинет' })

const MIN_PASSWORD = 10
const ROLES: UserRole[] = ['manager', 'courier', 'admin']
const ROLE_HINT: Record<UserRole, string> = {
  admin: 'Всё, включая деньги, наценку и сотрудников',
  manager: 'Заказы, каталог, остатки, партнёр. Без прибыли',
  courier: 'Только назначенные ему доставки',
}

const api = useUsersApi()
const auth = useAuthStore()
const toast = useToast()

const users = ref<StaffUser[]>([])
const loadError = ref('')
const isSaving = ref(false)
const form = reactive({ login: '', name: '', role: 'courier' as UserRole, password: '' })
// Сотрудник, которому сейчас задают новый пароль
const passwordFor = ref<number | null>(null)
const newPassword = ref('')

// Пароль без похожих символов, чтобы его можно было продиктовать по телефону
function generatePassword() {
  const alphabet = 'abcdefghjkmnpqrstuvwxyz23456789'
  const values = crypto.getRandomValues(new Uint32Array(12))
  return Array.from(values, (value) => alphabet[value % alphabet.length]).join('')
}

async function load() {
  try {
    users.value = await api.listUsers()
  } catch (error) {
    loadError.value = errorMessage(error, 'Не удалось загрузить сотрудников')
  }
}

async function run(action: () => Promise<unknown>, success: string) {
  isSaving.value = true
  try {
    await action()
    toast.success(success)
    await load()
    return true
  } catch (error) {
    toast.error(errorMessage(error))
    return false
  } finally {
    isSaving.value = false
  }
}

async function create() {
  const ok = await run(
    () => api.createUser({ ...form, login: form.login.trim().toLowerCase(), name: form.name.trim() }),
    `Сотрудник добавлен. Передайте ему логин ${form.login} и пароль`,
  )
  if (ok) Object.assign(form, { login: '', name: '', role: 'courier', password: '' })
}

const changeRole = (user: StaffUser, role: UserRole) => run(() => api.updateUser(user.id, { role }), 'Роль изменена')

function toggleActive(user: StaffUser) {
  if (user.is_active && !confirm(`Отключить ${user.name}? Войти он больше не сможет.`)) return
  return run(() => api.updateUser(user.id, { is_active: !user.is_active }), user.is_active ? 'Отключён' : 'Включён')
}

async function savePassword(user: StaffUser) {
  const ok = await run(() => api.setPassword(user.id, newPassword.value), `Пароль для ${user.name} изменён`)
  if (ok) {
    passwordFor.value = null
    newPassword.value = ''
  }
}

function openPassword(user: StaffUser) {
  passwordFor.value = user.id
  newPassword.value = generatePassword()
}

onMounted(load)
</script>

<template>
  <div class="a-page">
    <div class="a-page-head">
      <div>
        <h1 class="a-title">Сотрудники</h1>
        <p class="a-muted">Вход у всех один: {{ useRequestURL().origin }}/login</p>
      </div>
    </div>

    <p v-if="loadError" class="a-error" role="alert">{{ loadError }}</p>

    <div class="layout">
      <section class="a-card list">
        <article v-for="user in users" :key="user.id" class="user" :class="{ 'is-off': !user.is_active }">
          <div class="user__info">
            <strong>{{ user.name }}</strong>
            <span class="a-muted">{{ user.login }} · {{ user.last_login_at ? `входил ${formatDateTime(user.last_login_at)}` : 'ещё не входил' }}</span>
            <span v-if="!user.is_active" class="a-badge a-badge--danger">Отключён</span>
          </div>
          <div class="user__actions">
            <select
              class="a-select"
              :value="user.role"
              :disabled="user.id === auth.user?.id || isSaving"
              :aria-label="`Роль: ${user.name}`"
              @change="changeRole(user, ($event.target as HTMLSelectElement).value as UserRole)"
            >
              <option v-for="role in ROLES" :key="role" :value="role">{{ ROLE_LABEL[role] }}</option>
            </select>
            <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="openPassword(user)">Новый пароль</button>
            <button
              v-if="user.id !== auth.user?.id"
              class="a-btn a-btn--small"
              :class="user.is_active ? 'a-btn--danger' : 'a-btn--ghost'"
              type="button"
              :disabled="isSaving"
              @click="toggleActive(user)"
            >
              {{ user.is_active ? 'Отключить' : 'Включить' }}
            </button>
          </div>
          <form v-if="passwordFor === user.id" class="user__password" @submit.prevent="savePassword(user)">
            <input
              v-model="newPassword"
              class="a-input"
              :minlength="MIN_PASSWORD"
              required
              autocomplete="new-password"
              aria-label="Новый пароль"
            >
            <button class="a-btn a-btn--small" type="submit" :disabled="isSaving">Сохранить</button>
            <button class="a-btn a-btn--ghost a-btn--small" type="button" @click="passwordFor = null">Отмена</button>
          </form>
        </article>
      </section>

      <form class="a-card" @submit.prevent="create">
        <h2 class="a-subtitle">Новый сотрудник</h2>
        <label class="a-field">
          <span class="a-field__label">Имя</span>
          <input v-model="form.name" class="a-input" required maxlength="80" placeholder="Сергей">
        </label>
        <label class="a-field">
          <span class="a-field__label">Логин</span>
          <input
            v-model="form.login"
            class="a-input"
            required
            pattern="[a-z0-9._\-]{3,32}"
            autocapitalize="none"
            placeholder="sergey"
          >
          <span class="a-field__hint">Латиница, цифры, точка и дефис</span>
        </label>
        <label class="a-field">
          <span class="a-field__label">Роль</span>
          <select v-model="form.role" class="a-select">
            <option v-for="role in ROLES" :key="role" :value="role">{{ ROLE_LABEL[role] }}</option>
          </select>
          <span class="a-field__hint">{{ ROLE_HINT[form.role] }}</span>
        </label>
        <label class="a-field">
          <span class="a-field__label">Пароль</span>
          <div class="password">
            <input v-model="form.password" class="a-input" required :minlength="MIN_PASSWORD" autocomplete="new-password">
            <button class="a-btn a-btn--ghost" type="button" @click="form.password = generatePassword()">Придумать</button>
          </div>
          <span class="a-field__hint">Не короче {{ MIN_PASSWORD }} символов</span>
        </label>
        <button class="a-btn" type="submit" :disabled="isSaving">Добавить</button>
      </form>
    </div>
  </div>
</template>

<style scoped lang="scss">
.layout {
  display: flex;
  flex-direction: column-reverse;
  gap: 16px;
}

.list {
  gap: 0;
  padding: 0;
}

.user {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;

  & + & {
    border-top: 1px solid var(--color-line);
  }

  &.is-off &__info strong {
    color: var(--color-text-muted);
  }

  &__info {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;

    .a-select {
      width: auto;
      min-height: 36px;
    }
  }

  &__password {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto auto;
    gap: 8px;
  }
}

.password {
  display: flex;
  gap: 8px;
}

@media (min-width: 1024px) {
  .layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 380px;
    align-items: start;
  }

  .user {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;

    &__password {
      grid-column: 1 / -1;
    }
  }
}
</style>
