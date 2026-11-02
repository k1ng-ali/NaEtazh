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
