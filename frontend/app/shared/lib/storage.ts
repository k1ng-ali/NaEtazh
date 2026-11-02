// localStorage бывает недоступен (приватный режим, запрет cookie), сайт должен работать и без него
export const readJson = <T>(key: string, fallback: T): T => {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

export const writeJson = (key: string, value: unknown) => {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // Корзина останется в памяти до закрытия вкладки
  }
}
