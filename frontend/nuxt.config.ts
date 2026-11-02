export default defineNuxtConfig({
  compatibilityDate: '2026-11-01',
  modules: ['@pinia/nuxt'],
  // Компоненты импортируются явно из фич
  components: false,
  css: ['@fontsource-variable/golos-text', '~/assets/scss/main.scss'],
  typescript: {
    strict: true,
  },
  // Админке не нужен серверный рендеринг: токен живёт только в браузере
  routeRules: {
    '/admin/**': { ssr: false },
    // Корзина и корпус живут в localStorage, на сервере их нет
    '/cart': { ssr: false },
    '/checkout': { ssr: false },
    '/k/**': { ssr: false },
  },
  runtimeConfig: {
    // NUXT_API_INTERNAL_URL: адрес API для серверного рендеринга
    apiInternalUrl: 'http://localhost:8000/api/v1',
    public: {
      // NUXT_PUBLIC_API_URL: адрес API для браузера
      apiUrl: 'http://localhost:8000/api/v1',
      // NUXT_PUBLIC_MEDIA_URL: откуда брать загруженные фото, на сервере пусто (тот же домен)
      mediaUrl: 'http://localhost:8000',
      // NUXT_PUBLIC_SITE_URL: адрес сайта для QR-кодов корпусов
      siteUrl: 'http://localhost:3000',
    },
  },
  app: {
    head: {
      htmlAttrs: { lang: 'ru' },
      title: 'СтройБаза97',
      meta: [
        { name: 'description', content: 'Стройматериалы с доставкой и подъёмом в квартиру' },
        { name: 'theme-color', content: '#111111' },
      ],
    },
  },
})
