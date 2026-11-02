import { useAdminHttp } from '../shared/http'
import type { AdminBuilding, AdminComplex, BuildingPayload, ComplexPayload, Tariff, TariffPayload } from './types'

export const useLocationsApi = () => {
  const http = useAdminHttp()

  return {
    listComplexes: () => http<AdminComplex[]>('/admin/complexes/'),
    createComplex: (payload: ComplexPayload) =>
      http<AdminComplex>('/admin/complexes/', { method: 'POST', body: payload }),
    createBuilding: (complexId: number, payload: BuildingPayload) =>
      http<AdminBuilding>(`/admin/complexes/${complexId}/buildings`, { method: 'POST', body: payload }),
    updateBuilding: (id: number, payload: Partial<BuildingPayload>) =>
      http<AdminBuilding>(`/admin/buildings/${id}`, { method: 'PATCH', body: payload }),

    listTariffs: () => http<Tariff[]>('/admin/tariffs/'),
    saveTariff: (payload: TariffPayload) => http<Tariff>('/admin/tariffs/', { method: 'PUT', body: payload }),
    deleteTariff: (id: number) => http<void>(`/admin/tariffs/${id}`, { method: 'DELETE' }),
  }
}
