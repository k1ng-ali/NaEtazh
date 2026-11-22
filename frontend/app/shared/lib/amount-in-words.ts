// Сумма прописью для накладной: 1380.5 → «Одна тысяча триста восемьдесят рублей 50 копеек»

const ONES_MALE = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
const ONES_FEMALE = ['', 'одна', 'две', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
const TEENS = [
  'десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать',
  'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать',
]
const TENS = ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
const HUNDREDS = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот', 'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']

// Разряды: [одна, две-четыре, пять и больше], женский ли род
const SCALES: { forms: [string, string, string]; female: boolean }[] = [
  { forms: ['', '', ''], female: false },
  { forms: ['тысяча', 'тысячи', 'тысяч'], female: true },
  { forms: ['миллион', 'миллиона', 'миллионов'], female: false },
  { forms: ['миллиард', 'миллиарда', 'миллиардов'], female: false },
]

export function plural(value: number, forms: [string, string, string]) {
  const mod100 = value % 100
  const mod10 = value % 10
  if (mod100 >= 11 && mod100 <= 14) return forms[2]
  if (mod10 === 1) return forms[0]
  if (mod10 >= 2 && mod10 <= 4) return forms[1]
  return forms[2]
}

function triadWords(value: number, female: boolean) {
  const words = [HUNDREDS[Math.floor(value / 100)]]
  const rest = value % 100
  if (rest >= 10 && rest < 20) {
    words.push(TEENS[rest - 10])
  } else {
    words.push(TENS[Math.floor(rest / 10)], (female ? ONES_FEMALE : ONES_MALE)[rest % 10])
  }
  return words.filter((word): word is string => Boolean(word))
}

export function integerInWords(value: number) {
  if (value === 0) return 'ноль'
  const words: string[] = []
  let rest = Math.floor(value)
  for (let scale = 0; rest > 0 && scale < SCALES.length; scale++) {
    const triad = rest % 1000
    const scaleWords = SCALES[scale]
    if (triad && scaleWords) {
      words.unshift(...triadWords(triad, scaleWords.female), plural(triad, scaleWords.forms))
    }
    rest = Math.floor(rest / 1000)
  }
  return words.filter(Boolean).join(' ')
}

export function amountInWords(amount: string | number) {
  // Считаем в копейках, чтобы не ловить погрешность float
  const kopecks = Math.round(Number(amount) * 100)
  const rubles = Math.floor(kopecks / 100)
  const cents = kopecks % 100
  const text = `${integerInWords(rubles)} ${plural(rubles, ['рубль', 'рубля', 'рублей'])} ${String(cents).padStart(2, '0')} ${plural(cents, ['копейка', 'копейки', 'копеек'])}`
  return text.charAt(0).toUpperCase() + text.slice(1)
}
