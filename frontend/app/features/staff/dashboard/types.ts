export interface Dashboard {
  date_from: string
  date_to: string
  orders: number
  delivered: number
  canceled: number
  waiting: number
  revenue: string
  profit: string
  profit_complete: boolean
  avg_check: string
  days: { date: string; orders: number; revenue: string }[]
  buildings: { name: string; orders: number; revenue: string }[]
  couriers_today: { name: string; delivered: number; cash: string }[]
}
