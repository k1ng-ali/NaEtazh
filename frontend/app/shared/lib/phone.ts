// Российские номера: +7 — код страны, 8 — то же самое при звонке внутри страны.
// Поэтому «8 912…», «7 912…» и «912…» — один и тот же номер +7 (912) …
// Исключение — 8-800 и подобные бесплатные номера: их принято писать с восьмёркой.

export interface PhoneFormatOptions {
  // Не заменять 8 на +7: для телефона магазина, например 8 (800) 555-35-35
  keepEight?: boolean
}

const MAX_DIGITS = 11

export const onlyDigits = (value: string) => value.replace(/\D/g, '')

/** Цифры номера с кодом страны в начале: «89123456789» → «79123456789», «912» → «7912». */
export function phoneDigits(value: string, options: PhoneFormatOptions = {}): string {
  let digits = onlyDigits(value)
  if (!digits) return ''
  if (digits[0] === '8' && !options.keepEight) digits = `7${digits.slice(1)}`
  else if (digits[0] !== '7' && digits[0] !== '8') digits = `7${digits}`
  return digits.slice(0, MAX_DIGITS)
}

/** Номер по мере ввода: «+7», «+7 (912», «+7 (912) 345-67-89», «8 (800) 555-35-35». */
export function formatPhone(value: string, options: PhoneFormatOptions = {}): string {
  const digits = phoneDigits(value, options)
  if (!digits) return ''
  const prefix = digits[0] === '8' ? '8' : '+7'
  const rest = digits.slice(1)
  let result = prefix
  if (rest.length) result += ` (${rest.slice(0, 3)}`
  if (rest.length >= 3) result += ')'
  if (rest.length > 3) result += ` ${rest.slice(3, 6)}`
  if (rest.length > 6) result += `-${rest.slice(6, 8)}`
  if (rest.length > 8) result += `-${rest.slice(8, 10)}`
  return result
}

/** Позиция в отформатированной строке сразу после count-й цифры. */
export function caretAfterDigits(formatted: string, count: number): number {
  if (count <= 0) return formatted.startsWith('+') ? 1 : 0
  let seen = 0
  for (let index = 0; index < formatted.length; index += 1) {
    if (/\d/.test(formatted[index]!)) {
      seen += 1
      if (seen === count) return index + 1
    }
  }
  return formatted.length
}
