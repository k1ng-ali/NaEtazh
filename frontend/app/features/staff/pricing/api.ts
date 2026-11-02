import { useStaffHttp } from '../shared/http'
import type { PricingRule, PricingRulePayload, PricingRuleSaveResult } from './types'

export const usePricingApi = () => {
  const http = useStaffHttp()

  return {
    listRules: () => http<PricingRule[]>('/admin/pricing-rules/'),
    saveRule: (payload: PricingRulePayload) =>
      http<PricingRuleSaveResult>('/admin/pricing-rules/', { method: 'PUT', body: payload }),
    deleteRule: (id: number) => http<void>(`/admin/pricing-rules/${id}`, { method: 'DELETE' }),
  }
}
