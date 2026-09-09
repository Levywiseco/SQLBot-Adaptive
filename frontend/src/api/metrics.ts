import { request } from '@/utils/request'

export interface MetricPageQuery {
  keyword?: string
  status?: string
  datasource_id?: number
}

export const metricsApi = {
  page: (page: number, size: number, params: MetricPageQuery = {}) =>
    request.get(`/system/metrics/page/${page}/${size}`, { params }),
  detail: (id: number | string) => request.get(`/system/metrics/${id}`),
  create: (data: any) => request.post('/system/metrics', data),
  update: (id: number | string, data: any) => request.put(`/system/metrics/${id}`, data),
  publish: (id: number | string, versionId: number | string, reviewNote: string) =>
    request.post(`/system/metrics/${id}/versions/${versionId}/publish`, {
      review_note: reviewNote,
    }),
  archive: (id: number | string) => request.delete(`/system/metrics/${id}`),
  restore: (id: number | string) => request.post(`/system/metrics/${id}/restore`),
}
