const priceFormat = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 })
const quantityFormat = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 3 })
const dateTimeFormat = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' })

// API отдаёт деньги строкой, чтобы не терять точность
export const formatPrice = (value: string | number) => `${priceFormat.format(Number(value))} ₽`

export const formatQuantity = (value: string | number) => quantityFormat.format(Number(value))

export const formatDateTime = (value: string) => dateTimeFormat.format(new Date(value))
