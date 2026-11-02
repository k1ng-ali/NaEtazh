import type { LiftingType } from '~/features/cart/types'
import type { ContactChannel, DeliverySlot, MissingItemPolicy, OrderStatus } from './types'

// Подписи общие для витрины и админки
export const ORDER_STATUS: Record<OrderStatus, string> = {
  new: 'Принят',
  checking: 'Проверяем наличие',
  confirmed: 'Подтверждён',
  in_delivery: 'В пути',
  delivered: 'Доставлен',
  canceled: 'Отменён',
}

export const DELIVERY_SLOT: Record<DeliverySlot, string> = {
  morning: 'Утро, 9–12',
  day: 'День, 12–16',
  evening: 'Вечер, 16–20',
}

export const LIFTING: Record<LiftingType, string> = {
  none: 'Без подъёма, оставим у подъезда',
  lift: 'Поднять на грузовом лифте',
  stairs: 'Поднять по лестнице',
}

export const CONTACT_CHANNEL: Record<ContactChannel, string> = {
  call: 'Звонок',
  whatsapp: 'WhatsApp',
  telegram: 'Telegram',
}

export const MISSING_ITEM_POLICY: Record<MissingItemPolicy, string> = {
  call: 'Позвонить и решить вместе',
  replace: 'Заменить аналогом не дороже',
  skip: 'Привезти без этого товара',
}

export const AVAILABILITY = {
  in_stock: { label: 'В наличии', modifier: 'success' },
  // Срок привоза от партнёра подтверждает менеджер, поэтому без обещания дней
  on_order: { label: 'Под заказ', modifier: 'warning' },
  unavailable: { label: 'Нет в наличии', modifier: 'danger' },
} as const
