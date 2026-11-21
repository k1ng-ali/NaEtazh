export interface PricingRule {
  id: number
  category_id: number | null
  markup_percent: string
  min_profit: string
  updated_at: string
}

export interface PricingRulePayload {
  category_id: number | null
  markup_percent: string
  min_profit: string
}

export interface PricingRuleSaveResult {
  rule: PricingRule
  updated_prices: number
}

export interface ProductPrice {
  product_id: number
  product_name: string
  product_sku: string
  price: string
  min_profit: string
  // Цена на витрине сейчас: точная или поднятая из-за закупки
  sale_price: string
  cost: string | null
  // Менеджер поставил цену вручную, точная цена не действует
  is_price_manual: boolean
  updated_at: string
}

export interface ProductPricePayload {
  product_id: number
  price: string
  min_profit: string
}
