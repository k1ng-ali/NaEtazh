// Повторяет app/core/pricing.py, только для подсказки в форме. Настоящую цену считает бэкенд
// Допуск убирает погрешность float: 1150 × 1,2 не должно стать 1381
export const calcSalePrice = (cost: number, markupPercent: number, minProfit: number) =>
  Math.ceil(Math.max(cost * (1 + markupPercent / 100), cost + minProfit) - 1e-6)
