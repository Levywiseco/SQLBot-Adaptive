<script lang="ts" setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus-secondary'
import { learningApi } from '@/api/adaptive'
import { formatTimestamp } from '@/utils/date'
import EmptyBackground from '@/views/dashboard/common/EmptyBackground.vue'

const { t } = useI18n()
const loading = ref(false)
const rows = ref<any[]>([])
const stats = ref<any>({ by_status: {}, pending_jobs: 0 })
const statusFilter = ref('candidate')
const typeFilter = ref('')
const detailVisible = ref(false)
const detail = ref<any>({})
const pageInfo = reactive({ currentPage: 1, pageSize: 10, total: 0 })

const load = async () => {
  loading.value = true
  try {
    const [page, currentStats] = await Promise.all([
      learningApi.page(pageInfo.currentPage, pageInfo.pageSize, {
        status: statusFilter.value || undefined,
        candidate_type: typeFilter.value || undefined,
      }),
      learningApi.stats(),
    ])
    rows.value = page.data || []
    pageInfo.total = page.total_count || 0
    stats.value = currentStats || { by_status: {}, pending_jobs: 0 }
  } finally {
    loading.value = false
  }
}

const resetAndLoad = () => {
  pageInfo.currentPage = 1
  load()
}

const reviewNote = async (title: string) => {
  return ElMessageBox.prompt(t('learning.review_note_hint'), title, {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    inputType: 'textarea',
    inputValidator: (value: string) => value.trim().length >= 3 || t('learning.review_note_required'),
  }).catch(() => null)
}

const approve = async (row: any) => {
  const result = await reviewNote(t('learning.approve'))
  if (!result) return
  await learningApi.approve(row.id, result.value.trim())
  ElMessage.success(
    row.candidate_type === 'metric_change'
      ? t('learning.metric_change_accepted')
      : t('learning.approved')
  )
  await load()
}

const reject = async (row: any) => {
  const result = await reviewNote(t('learning.reject'))
  if (!result) return
  await learningApi.reject(row.id, result.value.trim())
  ElMessage.success(t('learning.rejected'))
  await load()
}

const revoke = async (row: any) => {
  const result = await reviewNote(t('learning.revoke'))
  if (!result) return
  await learningApi.revoke(row.id, result.value.trim())
  ElMessage.success(t('learning.revoked'))
  await load()
}

const showDetail = async (row: any) => {
  detail.value = await learningApi.detail(row.id)
  detailVisible.value = true
}

const statusType = (status: string) => {
  if (status === 'active') return 'success'
  if (status === 'candidate') return 'warning'
  if (status === 'rejected' || status === 'revoked') return 'danger'
  return 'info'
}

const validationText = (row: any) => {
  const known = ['awaiting_review', 'approved', 'requires_metric_version', 'rejected', 'revoked']
  return known.includes(row.validation_status)
    ? t(`learning.validation_${row.validation_status}`)
    : row.validation_message || row.validation_status
}

onMounted(load)
</script>

<template>
  <div v-loading="loading" class="learning-page">
    <section class="learning-heading">
      <div>
        <h1>{{ t('learning.center') }}</h1>
        <p>{{ t('learning.description') }}</p>
      </div>
    </section>

    <section class="stats-grid">
      <div class="stat-card"><span>{{ t('learning.pending') }}</span><strong>{{ stats.by_status?.candidate || 0 }}</strong></div>
      <div class="stat-card"><span>{{ t('learning.active') }}</span><strong>{{ stats.by_status?.active || 0 }}</strong></div>
      <div class="stat-card"><span>{{ t('learning.rejected') }}</span><strong>{{ stats.by_status?.rejected || 0 }}</strong></div>
      <div class="stat-card"><span>{{ t('learning.pending_jobs') }}</span><strong>{{ stats.pending_jobs || 0 }}</strong></div>
    </section>

    <el-alert class="governance-rule" :title="t('learning.governance_rule')" type="info" :closable="false" show-icon />

    <section class="learning-toolbar">
      <el-select v-model="statusFilter" clearable :placeholder="t('learning.all_statuses')" @change="resetAndLoad">
        <el-option :label="t('learning.status_candidate')" value="candidate" />
        <el-option :label="t('learning.status_active')" value="active" />
        <el-option :label="t('learning.status_approved')" value="approved" />
        <el-option :label="t('learning.status_rejected')" value="rejected" />
        <el-option :label="t('learning.status_revoked')" value="revoked" />
      </el-select>
      <el-select v-model="typeFilter" clearable :placeholder="t('learning.all_types')" @change="resetAndLoad">
        <el-option v-for="item in ['confirmed_answer', 'correction_rule', 'metric_change', 'shared_example', 'personal_preference']" :key="item" :label="t(`learning.type_${item}`)" :value="item" />
      </el-select>
      <el-button secondary @click="resetAndLoad">{{ t('common.search') }}</el-button>
    </section>

    <section class="learning-table">
      <el-table :data="rows" @row-dblclick="showDetail">
        <el-table-column :label="t('learning.type')" width="130">
          <template #default="scope">{{ t(`learning.type_${scope.row.candidate_type}`) }}</template>
        </el-table-column>
        <el-table-column :label="t('learning.question')" min-width="175" show-overflow-tooltip>
          <template #default="scope">{{ scope.row.proposed_content?.question || '—' }}</template>
        </el-table-column>
        <el-table-column :label="t('learning.correction')" min-width="195" show-overflow-tooltip>
          <template #default="scope">{{ scope.row.proposed_content?.correction || '—' }}</template>
        </el-table-column>
        <el-table-column :label="t('learning.validation')" min-width="155" show-overflow-tooltip>
          <template #default="scope">{{ validationText(scope.row) }}</template>
        </el-table-column>
        <el-table-column :label="t('learning.status')" width="100">
          <template #default="scope"><el-tag :type="statusType(scope.row.status)">{{ t(`learning.status_${scope.row.status}`) }}</el-tag></template>
        </el-table-column>
        <el-table-column :label="t('learning.created_at')" width="145">
          <template #default="scope">{{ formatTimestamp(scope.row.created_at, 'YYYY-MM-DD HH:mm:ss') }}</template>
        </el-table-column>
        <el-table-column fixed="right" :label="t('ds.actions')" width="185">
          <template #default="scope">
            <div class="row-actions">
              <el-button link @click.stop="showDetail(scope.row)">{{ t('learning.detail') }}</el-button>
              <template v-if="scope.row.status === 'candidate'">
                <el-button link type="success" @click.stop="approve(scope.row)">{{ t('learning.approve') }}</el-button>
                <el-button link type="danger" @click.stop="reject(scope.row)">{{ t('learning.reject') }}</el-button>
              </template>
              <el-button v-if="['active', 'approved'].includes(scope.row.status)" link type="danger" @click.stop="revoke(scope.row)">{{ t('learning.revoke') }}</el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty><EmptyBackground :description="t('learning.empty')" img-type="noneWhite" /></template>
      </el-table>
    </section>

    <div v-if="pageInfo.total" class="pagination-container">
      <el-pagination v-model:current-page="pageInfo.currentPage" v-model:page-size="pageInfo.pageSize" :page-sizes="[10, 20, 30]" background layout="total, sizes, prev, pager, next" :total="pageInfo.total" @size-change="load" @current-change="load" />
    </div>
  </div>

  <el-drawer v-model="detailVisible" :title="t('learning.detail')" size="680px">
    <el-descriptions v-if="detail.id" :column="1" border>
      <el-descriptions-item :label="t('learning.type')">{{ t(`learning.type_${detail.candidate_type}`) }}</el-descriptions-item>
      <el-descriptions-item :label="t('learning.status')">{{ t(`learning.status_${detail.status}`) }}</el-descriptions-item>
      <el-descriptions-item :label="t('learning.question')">{{ detail.proposed_content?.question || '—' }}</el-descriptions-item>
      <el-descriptions-item :label="t('learning.correction')">{{ detail.proposed_content?.correction || '—' }}</el-descriptions-item>
      <el-descriptions-item label="SQL"><pre>{{ detail.proposed_content?.sql || '—' }}</pre></el-descriptions-item>
      <el-descriptions-item :label="t('learning.provenance')"><pre>{{ JSON.stringify({ metrics: detail.proposed_content?.metric_refs, memories: detail.proposed_content?.memory_refs }, null, 2) }}</pre></el-descriptions-item>
      <el-descriptions-item :label="t('learning.review_note')">{{ detail.review_note || '—' }}</el-descriptions-item>
    </el-descriptions>
  </el-drawer>
</template>

<style lang="less" scoped>
.learning-page { height: 100%; padding: 24px; background: #f7f8fa; overflow: auto; }
.learning-heading { margin-bottom: 16px; }
.learning-heading h1 { margin: 0 0 6px; font-size: 24px; color: #1f2329; }
.learning-heading p { margin: 0; color: #646a73; font-size: 14px; }
.stats-grid { display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 12px; margin-bottom: 16px; }
.stat-card { display: flex; align-items: center; justify-content: space-between; padding: 16px; background: #fff; border: 1px solid #e5e6eb; border-radius: 10px; color: #646a73; }
.stat-card strong { font-size: 24px; color: #1f2329; }
.governance-rule { margin-bottom: 16px; }
.learning-toolbar { display: flex; gap: 12px; padding: 16px; background: #fff; border: 1px solid #e5e6eb; border-bottom: 0; border-radius: 10px 10px 0 0; }
.learning-toolbar .ed-select { width: 220px; }
.learning-table { background: #fff; border: 1px solid #e5e6eb; border-radius: 0 0 10px 10px; overflow: hidden; }
.row-actions { display: flex; align-items: center; gap: 8px; }
.pagination-container { display: flex; justify-content: flex-end; padding: 16px 0; }
pre { margin: 0; white-space: pre-wrap; word-break: break-word; font-family: ui-monospace, monospace; font-size: 12px; }
@media (max-width: 900px) {
  .stats-grid { grid-template-columns: 1fr 1fr; }
  .learning-toolbar { flex-direction: column; }
  .learning-toolbar .ed-select { width: 100%; }
}
</style>
