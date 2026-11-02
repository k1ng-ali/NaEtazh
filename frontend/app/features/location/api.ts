import { useHttp } from '~/shared/api/http'
import type { Building } from './types'

export const useLocationApi = () => {
  const http = useHttp()

  return {
    getBuilding: (code: string) => http<Building>(`/buildings/${encodeURIComponent(code)}`),
  }
}
