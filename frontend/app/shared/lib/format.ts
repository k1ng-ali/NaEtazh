const priceFormat = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 })

// API отдаёт деньги строкой, чтобы не терять точность
export const formatPrice = (value: string | number) => `${priceFormat.format(Number(value))} ₽`
