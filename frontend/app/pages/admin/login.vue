<script setup lang="ts">
import '~/assets/scss/admin.scss'
import { reactive, ref } from 'vue'
import { useAuthStore } from '~/features/admin/auth/store'
import { errorMessage } from '~/features/admin/shared/errors'

definePageMeta({ layout: false, middleware: 'admin' })
useHead({ title: 'Вход | Админка СтройБаза97' })

const auth = useAuthStore()
const route = useRoute()

const form = reactive({ login: '', password: '' })
const isSubmitting = ref(false)
const errorText = ref('')

async function submit() {
  isSubmitting.value = true
  errorText.value = ''
  try {
    await auth.login({ login: form.login, password: form.password })
    const next = typeof route.query.next === 'string' && route.query.next.startsWith('/admin') ? route.query.next : '/admin/products'
    await navigateTo(next)
  } catch (error) {
    errorText.value = errorMessage(error)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="login">
    <form class="login__card a-card" @submit.prevent="submit">
      <div>
        <p class="login__logo">СтройБаза97</p>
        <h1 class="a-title">Вход для сотрудников</h1>
      </div>

      <label class="a-field">
        <span class="a-field__label">Логин</span>
        <input v-model="form.login" class="a-input" autocomplete="username" autocapitalize="none" required>
      </label>
      <label class="a-field">
        <span class="a-field__label">Пароль</span>
        <input v-model="form.password" class="a-input" type="password" autocomplete="current-password" required>
      </label>

      <p v-if="errorText" class="a-error" role="alert">{{ errorText }}</p>

      <button class="a-btn" type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Входим…' : 'Войти' }}
      </button>
    </form>
  </div>
</template>

<style scoped lang="scss">
.login {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 16px;
  background: var(--color-bg);

  &__card {
    gap: 16px;
    width: 100%;
    max-width: 400px;
    padding: 24px;
  }

  &__logo {
    margin-bottom: 4px;
    color: var(--color-text-muted);
    font-weight: 600;
  }
}
</style>
