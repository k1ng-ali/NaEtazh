export interface AdminBuilding {
  id: number
  complex_id: number
  name: string
  code: string
  floors: number | null
  cargo_lift_length_mm: number | null
}

export interface AdminComplex {
  id: number
  name: string
  slug: string
  address: string | null
  is_active: boolean
  buildings: AdminBuilding[]
}

export interface ComplexPayload {
  name: string
  address: string | null
}

export interface BuildingPayload {
  name: string
  floors: number | null
  cargo_lift_length_mm: number | null
}

export interface Tariff {
  id: number
  complex_id: number | null
  delivery_price: string
  delivery_free_from: string | null
  delivery_cost: string
  lift_price_per_100kg: string
  lift_min_price: string
  stairs_price_per_100kg_floor: string
  lifting_cost_percent: string
  updated_at: string
}

export type TariffPayload = Omit<Tariff, 'id' | 'updated_at'>
