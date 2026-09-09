import { request } from '@/utils/request'

export interface MemoryPayload {
  title: string
  content: string
  memory_type?: 'preference' | 'business_rule' | 'confirmed_example'
  scope?: 'personal' | 'workspace'
  keywords?: string[]
  dependencies?: string[]
  datasource_id?: number | null
  expires_at?: string | null
  priority?: number
}

export interface FeedbackPayload {
  chat_record_id: number
  feedback_type:
    | 'correct'
    | 'result_wrong'
    | 'metric_wrong'
    | 'remember_preference'
    | 'save_example'
  correction_text?: string
  memory_title?: string
  memory_content?: string
  memory_keywords?: string[]
  idempotency_key: string
}

export const memoryApi = {
  page: (page: number, size: number, params: Record<string, any> = {}) =>
    request.get(`/system/memories/page/${page}/${size}`, { params }),
  detail: (id: number | string) => request.get(`/system/memories/${id}`),
  create: (payload: MemoryPayload) => request.post('/system/memories', payload),
  update: (id: number | string, payload: Partial<MemoryPayload>) =>
    request.put(`/system/memories/${id}`, payload),
  status: (id: number | string, status: 'active' | 'paused') =>
    request.post(`/system/memories/${id}/status`, { status }),
  remove: (id: number | string) => request.delete(`/system/memories/${id}`),
}

export const feedbackApi = {
  create: (payload: FeedbackPayload) => request.post('/feedback', payload),
  page: (page: number, size: number) => request.get(`/feedback/page/${page}/${size}`),
}

export const learningApi = {
  page: (page: number, size: number, params: Record<string, any> = {}) =>
    request.get(`/system/learning/page/${page}/${size}`, { params }),
  detail: (id: number | string) => request.get(`/system/learning/${id}`),
  stats: () => request.get('/system/learning/stats'),
  approve: (id: number | string, review_note: string) =>
    request.post(`/system/learning/${id}/approve`, { review_note }),
  reject: (id: number | string, review_note: string) =>
    request.post(`/system/learning/${id}/reject`, { review_note }),
  revoke: (id: number | string, review_note: string) =>
    request.post(`/system/learning/${id}/revoke`, { review_note }),
}
