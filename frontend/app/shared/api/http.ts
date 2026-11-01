// Единая точка запросов к API, на сервере и в браузере адреса разные
export const useHttp = () => {
  const config = useRuntimeConfig()
  const baseURL = import.meta.server ? config.apiInternalUrl : config.public.apiUrl
  return $fetch.create({ baseURL })
}
