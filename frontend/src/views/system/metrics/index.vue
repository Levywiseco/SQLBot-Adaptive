<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { datasourceApi } from '@/api/datasource'
import { metricsApi } from '@/api/metrics'
import { formatTimestamp } from '@/utils/date'
import EmptyBackground from '@/views/dashboard/common/EmptyBackground.vue'
import icon_add_outlined from '@/assets/svg/icon_add_outlined.svg'
import IconOpeEdit from '@/assets/svg/icon_edit_outlined.svg'
import IconOpeDelete from '@/assets/svg/icon_delete.svg'
import icon_searchOutline_outlined from '@/assets/svg/icon_search-outline_outlined.svg'

interface MetricForm {
  id?: number | string | null
  code: string
  name: string
  aliases: string[]
  description: string
  datasource_id?: number
  expression: string
  aggregation: string
  time_field: string
  grain: string
  required_tables_text: string
  dimensions_text: string
  filters_text: string
  join_rules_text: string
  unit: string
}

interface PreviewForm {
  dimensions: string[]
  timeRange: string[]
  filtersText: string
  limit?: number
}

const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const rows = ref<any[]>([])
const datasources = ref<any[]>([])
const keyword = ref('')
const datasourceFilter = ref<number>()
const statusFilter = ref('')
const editVisible = ref(false)
const historyVisible = ref(false)
const historyMetric = ref<any>({ versions: [] })
const previewVisible = ref(false)
const previewLoading = ref(false)
const previewMetric = ref<any>({})
const previewPlan = ref<any>(null)
const previewForm = ref<PreviewForm>({
  dimensions: [],
  timeRange: [],
  filtersText: '[]',
  limit: undefined,
})
const formRef = ref()

const pageInfo = reactive({ currentPage: 1, pageSize: 10, total: 0 })

const emptyForm = (): MetricForm => ({
  id: null,
  code: '',
  name: '',
  aliases: [],
  description: '',
  datasource_id: undefined,
  expression: '',
  aggregation: 'SUM',
  time_field: '',
  grain: '',
  required_tables_text: '',
  dimensions_text: '',
  filters_text: '[]',
  join_rules_text: '[]',
  unit: '',
})

const form = ref<MetricForm>(emptyForm())
const drawerTitle = computed(() =>
  form.value.id ? t('metric.edit_metric') : t('metric.create_metric')
)

const rules = {
  code: [{ required: true, message: t('metric.code_required'), trigger: 'blur' }],
  name: [{ required: true, message: t('metric.name_required'), trigger: 'blur' }],
  datasource_id: [{ required: true, message: t('metric.datasource_required'), trigger: 'change' }],
  expression: [{ required: true, message: t('metric.expression_required'), trigger: 'blur' }],
  required_tables_text: [
    { required: true, message: t('metric.required_tables_required'), trigger: 'blur' },
  ],
}

const splitList = (value: string) =>
  [...new Set(value.split(/[,，\n]/).map((item) => item.trim()).filter(Boolean))]

const parseJsonArray = (value: string, label: string) => {
  try {
    const parsed = JSON.parse(value || '[]')
    if (!Array.isArray(parsed)) throw new Error('not array')
    return parsed
  } catch {
    ElMessage.error(t('metric.invalid_json_array', { label }))
    throw new Error(`${label} must be a JSON array`)
  }
}

const load = async () => {
  loading.value = true
  try {
    const result = await metricsApi.page(pageInfo.currentPage, pageInfo.pageSize, {
      keyword: keyword.value || undefined,
      status: statusFilter.value || undefined,
      datasource_id: datasourceFilter.value,
    })
    rows.value = result.data || []
    pageInfo.total = result.total_count || 0
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  form.value = emptyForm()
  editVisible.value = true
}

const versionToForm = (metric: any): MetricForm => {
  const version = metric.latest_version || metric.current_version || {}
  return {
    id: metric.id,
    code: metric.code || '',
    name: metric.name || '',
    aliases: metric.aliases || [],
    description: metric.description || '',
    datasource_id: metric.datasource_id,
    expression: version.expression || '',
    aggregation: version.aggregation || 'SUM',
    time_field: version.time_field || '',
    grain: version.grain || '',
    required_tables_text: (version.required_tables || []).join(', '),
    dimensions_text: (version.dimensions || []).join(', '),
    filters_text: JSON.stringify(version.filters || [], null, 2),
    join_rules_text: JSON.stringify(version.join_rules || [], null, 2),
    unit: version.unit || '',
  }
}

const openEdit = async (row: any) => {
  loading.value = true
  try {
    const metric = await metricsApi.detail(row.id)
    form.value = versionToForm(metric)
    editVisible.value = true
  } finally {
    loading.value = false
  }
}

const makeCalculation = () => ({
  expression: form.value.expression.trim(),
  aggregation: form.value.aggregation,
  time_field: form.value.time_field.trim() || null,
  grain: form.value.grain.trim() || null,
  required_tables: splitList(form.value.required_tables_text),
  dimensions: splitList(form.value.dimensions_text),
  filters: parseJsonArray(form.value.filters_text, t('metric.filters')),
  join_rules: parseJsonArray(form.value.join_rules_text, t('metric.join_rules')),
  unit: form.value.unit.trim() || null,
})

const save = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const calculation = makeCalculation()
    const definition = {
      code: form.value.code.trim(),
      name: form.value.name.trim(),
      aliases: form.value.aliases,
      description: form.value.description.trim() || null,
      datasource_id: form.value.datasource_id,
    }
    if (form.value.id) {
      await metricsApi.update(form.value.id, { ...definition, calculation })
    } else {
      await metricsApi.create({ ...definition, ...calculation })
    }
    ElMessage.success(t('common.save_success'))
    editVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const publish = async (row: any) => {
  const draft = row.latest_version
  if (!draft || draft.status !== 'draft') return
  const result = await ElMessageBox.prompt(t('metric.publish_note_hint'), t('metric.publish_metric'), {
    confirmButtonText: t('metric.publish'),
    cancelButtonText: t('common.cancel'),
    inputType: 'textarea',
    inputValidator: (value: string) => value.trim().length >= 3 || t('metric.publish_note_required'),
  }).catch(() => null)
  if (!result) return
  await metricsApi.publish(row.id, draft.id, result.value.trim())
  ElMessage.success(t('metric.publish_success'))
  await load()
}

const archive = async (row: any) => {
  await ElMessageBox.confirm(t('metric.archive_confirm', { name: row.name }), {
    confirmButtonText: t('metric.archive'),
    cancelButtonText: t('common.cancel'),
    confirmButtonType: 'danger',
  })
  await metricsApi.archive(row.id)
  ElMessage.success(t('metric.archive_success'))
  await load()
}

const showHistory = async (row: any) => {
  historyMetric.value = await metricsApi.detail(row.id)
  historyVisible.value = true
}

const compilePreview = async () => {
  if (!previewMetric.value.id) return
  const filters = parseJsonArray(previewForm.value.filtersText, t('metric.runtime_filters'))
  const timeRange = previewForm.value.timeRange || []
  if (timeRange.length === 1) {
    ElMessage.error(t('metric.time_range_pair_required'))
    return
  }
  previewLoading.value = true
  try {
    previewPlan.value = await metricsApi.previewQueryPlan(previewMetric.value.id, {
      version_id: previewMetric.value.current_version_id,
      dimensions: previewForm.value.dimensions,
      filters,
      time_range:
        timeRange.length === 2
          ? {
              start: timeRange[0],
              end: timeRange[1],
            }
          : null,
      limit: previewForm.value.limit || null,
    })
  } finally {
    previewLoading.value = false
  }
}

const openPreview = async (row: any) => {
  previewLoading.value = true
  previewVisible.value = true
  previewPlan.value = null
  try {
    previewMetric.value = await metricsApi.detail(row.id)
    previewForm.value = {
      dimensions: [...(previewMetric.value.current_version?.dimensions || [])],
      timeRange: [],
      filtersText: '[]',
      limit: undefined,
    }
    await compilePreview()
  } finally {
    previewLoading.value = false
  }
}

const statusType = (status: string) => {
  if (status === 'published') return 'success'
  if (status === 'draft') return 'warning'
  if (status === 'superseded') return 'info'
  return 'info'
}

const resetAndLoad = () => {
  pageInfo.currentPage = 1
  load()
}

onMounted(async () => {
  datasources.value = (await datasourceApi.list()) || []
  await load()
})
</script>

<template>
  <div v-loading="loading" class="metric-page">
    <section class="metric-heading">
      <div>
        <h1>{{ t('metric.catalog') }}</h1>
        <p>{{ t('metric.catalog_description') }}</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <template #icon><icon_add_outlined /></template>
        {{ t('metric.create_metric') }}
      </el-button>
    </section>

    <section class="metric-toolbar">
      <el-input
        v-model="keyword"
        clearable
        class="search-input"
        :placeholder="t('metric.search_placeholder')"
        @keyup.enter="resetAndLoad"
        @clear="resetAndLoad"
      >
        <template #prefix><el-icon><icon_searchOutline_outlined /></el-icon></template>
      </el-input>
      <el-select
        v-model="datasourceFilter"
        clearable
        :placeholder="t('metric.all_datasources')"
        @change="resetAndLoad"
      >
        <el-option v-for="item in datasources" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select
        v-model="statusFilter"
        clearable
        :placeholder="t('metric.all_statuses')"
        @change="resetAndLoad"
      >
        <el-option :label="t('metric.status_published')" value="published" />
        <el-option :label="t('metric.status_draft')" value="draft" />
        <el-option :label="t('metric.status_archived')" value="archived" />
      </el-select>
      <el-button secondary @click="resetAndLoad">{{ t('common.search') }}</el-button>
    </section>

    <section class="metric-table">
      <el-table :data="rows" @row-dblclick="openEdit">
        <el-table-column prop="name" :label="t('metric.name')" min-width="190">
          <template #default="scope">
            <div class="metric-name">{{ scope.row.name }}</div>
            <div class="metric-code">{{ scope.row.code }}</div>
          </template>
        </el-table-column>
        <el-table-column :label="t('metric.aliases')" min-width="180">
          <template #default="scope">
            <span class="muted">{{ (scope.row.aliases || []).join('、') || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="datasource_name" :label="t('metric.datasource')" min-width="160" />
        <el-table-column :label="t('metric.version')" width="130">
          <template #default="scope">
            <span v-if="scope.row.current_version">v{{ scope.row.current_version.version }}</span>
            <span v-else>—</span>
            <el-tag v-if="scope.row.has_draft" class="draft-tag" size="small" type="warning">
              {{ t('metric.has_draft') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('metric.status')" width="120">
          <template #default="scope">
            <el-tag :type="statusType(scope.row.status)" effect="light">
              {{ t(`metric.status_${scope.row.status}`) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('metric.updated_at')" width="190">
          <template #default="scope">
            {{ formatTimestamp(scope.row.updated_at, 'YYYY-MM-DD HH:mm:ss') }}
          </template>
        </el-table-column>
        <el-table-column fixed="right" :label="t('ds.actions')" width="280">
          <template #default="scope">
            <div class="row-actions">
              <el-button link type="primary" @click.stop="showHistory(scope.row)">
                {{ t('metric.history') }}
              </el-button>
              <el-button
                v-if="scope.row.current_version"
                link
                type="primary"
                @click.stop="openPreview(scope.row)"
              >
                {{ t('metric.query_plan') }}
              </el-button>
              <el-button
                v-if="scope.row.latest_version?.status === 'draft'"
                link
                type="success"
                @click.stop="publish(scope.row)"
              >
                {{ t('metric.publish') }}
              </el-button>
              <el-tooltip :content="t('datasource.edit')" placement="top">
                <el-icon class="action-icon" @click.stop="openEdit(scope.row)"><IconOpeEdit /></el-icon>
              </el-tooltip>
              <el-tooltip :content="t('metric.archive')" placement="top">
                <el-icon class="action-icon" @click.stop="archive(scope.row)"><IconOpeDelete /></el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <EmptyBackground :description="t('metric.empty')" img-type="noneWhite" />
        </template>
      </el-table>
    </section>

    <div v-if="pageInfo.total" class="pagination-container">
      <el-pagination
        v-model:current-page="pageInfo.currentPage"
        v-model:page-size="pageInfo.pageSize"
        :page-sizes="[10, 20, 30]"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="pageInfo.total"
        @size-change="load"
        @current-change="load"
      />
    </div>
  </div>

  <el-drawer v-model="editVisible" :title="drawerTitle" size="720px" destroy-on-close>
    <el-alert :title="t('metric.version_rule')" type="info" :closable="false" show-icon />
    <el-form ref="formRef" class="metric-form" :model="form" :rules="rules" label-position="top">
      <div class="form-grid two-columns">
        <el-form-item prop="name" :label="t('metric.name')">
          <el-input v-model="form.name" maxlength="255" />
        </el-form-item>
        <el-form-item prop="code" :label="t('metric.code')">
          <el-input v-model="form.code" :disabled="!!form.id" placeholder="net_sales" />
        </el-form-item>
      </div>
      <el-form-item :label="t('metric.aliases')">
        <el-select v-model="form.aliases" multiple filterable allow-create default-first-option>
          <el-option v-for="alias in form.aliases" :key="alias" :label="alias" :value="alias" />
        </el-select>
      </el-form-item>
      <el-form-item :label="t('metric.description')">
        <el-input v-model="form.description" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item prop="datasource_id" :label="t('metric.datasource')">
        <el-select v-model="form.datasource_id" :disabled="!!form.id" filterable>
          <el-option v-for="item in datasources" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
      </el-form-item>

      <div class="section-title">{{ t('metric.calculation') }}</div>
      <el-form-item prop="expression" :label="t('metric.expression')">
        <el-input
          v-model="form.expression"
          type="textarea"
          :rows="5"
          placeholder="orders.amount - COALESCE(orders.refund_amount, 0)"
        />
        <div class="field-hint">{{ t('metric.expression_hint') }}</div>
      </el-form-item>
      <div class="form-grid three-columns">
        <el-form-item :label="t('metric.aggregation')">
          <el-select v-model="form.aggregation">
            <el-option v-for="item in ['SUM', 'COUNT', 'COUNT_DISTINCT', 'AVG', 'MIN', 'MAX', 'CUSTOM']" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('metric.unit')"><el-input v-model="form.unit" /></el-form-item>
        <el-form-item :label="t('metric.grain')"><el-input v-model="form.grain" /></el-form-item>
      </div>
      <el-form-item prop="required_tables_text" :label="t('metric.required_tables')">
        <el-input v-model="form.required_tables_text" :placeholder="t('metric.comma_separated')" />
      </el-form-item>
      <div class="form-grid two-columns">
        <el-form-item :label="t('metric.time_field')"><el-input v-model="form.time_field" /></el-form-item>
        <el-form-item :label="t('metric.dimensions')"><el-input v-model="form.dimensions_text" :placeholder="t('metric.comma_separated')" /></el-form-item>
      </div>
      <div class="form-grid two-columns">
        <el-form-item :label="t('metric.filters')"><el-input v-model="form.filters_text" type="textarea" :rows="5" /></el-form-item>
        <el-form-item :label="t('metric.join_rules')"><el-input v-model="form.join_rules_text" type="textarea" :rows="5" /></el-form-item>
      </div>
    </el-form>
    <template #footer>
      <el-button secondary @click="editVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="saving" @click="save">{{ t('common.save') }}</el-button>
    </template>
  </el-drawer>

  <el-drawer v-model="historyVisible" :title="t('metric.version_history')" size="720px">
    <div class="history-heading">
      <strong>{{ historyMetric.name }}</strong>
      <span>{{ historyMetric.code }}</span>
    </div>
    <el-table :data="historyMetric.versions || []">
      <el-table-column :label="t('metric.version')" width="90">
        <template #default="scope">v{{ scope.row.version }}</template>
      </el-table-column>
      <el-table-column :label="t('metric.status')" width="130">
        <template #default="scope"><el-tag :type="statusType(scope.row.status)">{{ t(`metric.status_${scope.row.status}`) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="expression" :label="t('metric.expression')" min-width="260" show-overflow-tooltip />
      <el-table-column prop="review_note" :label="t('metric.review_note')" min-width="180" show-overflow-tooltip />
      <el-table-column :label="t('metric.created_at')" width="180">
        <template #default="scope">{{ formatTimestamp(scope.row.created_at, 'YYYY-MM-DD HH:mm:ss') }}</template>
      </el-table-column>
    </el-table>
  </el-drawer>

  <el-drawer
    v-model="previewVisible"
    :title="t('metric.query_plan_preview')"
    size="760px"
    destroy-on-close
  >
    <div v-loading="previewLoading" class="preview-panel">
      <el-alert
        :title="t('metric.query_plan_description')"
        :description="t('metric.query_plan_scope')"
        type="info"
        :closable="false"
        show-icon
      />
      <div class="preview-metric-heading">
        <div>
          <strong>{{ previewMetric.name }}</strong>
          <span>{{ previewMetric.code }}</span>
        </div>
        <el-tag v-if="previewMetric.current_version" type="success">
          v{{ previewMetric.current_version.version }}
        </el-tag>
      </div>
      <el-form label-position="top">
        <el-form-item :label="t('metric.dimensions')">
          <el-select v-model="previewForm.dimensions" multiple clearable>
            <el-option
              v-for="dimension in previewMetric.current_version?.dimensions || []"
              :key="dimension"
              :label="dimension"
              :value="dimension"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('metric.time_range')">
          <el-date-picker
            v-model="previewForm.timeRange"
            type="datetimerange"
            value-format="YYYY-MM-DDTHH:mm:ss"
            start-placeholder="Start"
            end-placeholder="End"
          />
        </el-form-item>
        <div class="form-grid two-columns">
          <el-form-item :label="t('metric.runtime_filters')">
            <el-input v-model="previewForm.filtersText" type="textarea" :rows="4" />
          </el-form-item>
          <el-form-item :label="t('metric.result_limit')">
            <el-input-number v-model="previewForm.limit" :min="1" :max="10000" controls-position="right" />
          </el-form-item>
        </div>
        <el-button type="primary" :loading="previewLoading" @click="compilePreview">
          {{ t('metric.compile_plan') }}
        </el-button>
      </el-form>

      <template v-if="previewPlan">
        <div class="plan-meta">
          <el-tag effect="plain">{{ previewPlan.compiler }}</el-tag>
          <span>metric_version_id: {{ previewPlan.metric_version_id }}</span>
          <span>{{ t('metric.sql_fingerprint') }}: {{ previewPlan.sql_fingerprint }}</span>
        </div>
        <div class="section-title">{{ t('metric.applied_filters') }}</div>
        <pre class="json-preview">{{ JSON.stringify(previewPlan.applied_filters, null, 2) }}</pre>
        <div class="section-title">{{ t('metric.compiled_sql') }}</div>
        <pre class="sql-preview">{{ previewPlan.sql }}</pre>
      </template>
    </div>
  </el-drawer>
</template>

<style lang="less" scoped>
.metric-page {
  height: 100%;
  padding: 24px;
  background: #f7f8fa;
  overflow: auto;
}
.metric-heading,
.metric-toolbar,
.row-actions,
.history-heading {
  display: flex;
  align-items: center;
}
.metric-heading {
  justify-content: space-between;
  margin-bottom: 20px;
  h1 { margin: 0 0 6px; font-size: 24px; line-height: 32px; color: #1f2329; }
  p { margin: 0; color: #646a73; font-size: 14px; }
}
.metric-toolbar {
  gap: 12px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e5e6eb;
  border-bottom: 0;
  border-radius: 10px 10px 0 0;
  .search-input { width: 280px; }
  .ed-select { width: 190px; }
}
.metric-table {
  background: #fff;
  border: 1px solid #e5e6eb;
  border-radius: 0 0 10px 10px;
  overflow: hidden;
}
.metric-name { font-weight: 500; color: #1f2329; }
.metric-code, .muted { color: #73849a; font-size: 12px; margin-top: 3px; }
.draft-tag { margin-left: 7px; }
.row-actions { gap: 8px; }
.action-icon { cursor: pointer; color: #646a73; }
.action-icon:hover { color: var(--ed-color-primary); }
.pagination-container { display: flex; justify-content: flex-end; padding: 16px 0; }
.metric-form { margin-top: 20px; }
.form-grid { display: grid; gap: 16px; }
.two-columns { grid-template-columns: 1fr 1fr; }
.three-columns { grid-template-columns: 1fr 1fr 1fr; }
.section-title { margin: 22px 0 14px; padding-top: 18px; border-top: 1px solid #e5e6eb; font-size: 16px; font-weight: 500; }
.field-hint { margin-top: 6px; color: #73849a; font-size: 12px; line-height: 18px; }
.history-heading { gap: 10px; margin-bottom: 16px; }
.history-heading span { color: #73849a; font-family: monospace; }
.preview-panel { min-height: 360px; }
.preview-metric-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 20px 0;
  padding-bottom: 14px;
  border-bottom: 1px solid #e5e6eb;
  div { display: flex; align-items: baseline; gap: 10px; }
  span { color: #73849a; font-family: monospace; }
}
.plan-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  margin-top: 22px;
  color: #646a73;
  font-family: monospace;
  font-size: 12px;
  span:last-child { overflow-wrap: anywhere; }
}
.sql-preview,
.json-preview {
  margin: 0;
  padding: 14px;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  background: #f7f8fa;
  color: #1f2329;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 12px;
  line-height: 1.65;
}
.json-preview { max-height: 180px; }
:deep(.ed-select) { width: 100%; }
:deep(.ed-date-editor) { width: 100%; }
@media (max-width: 900px) {
  .metric-heading, .metric-toolbar { align-items: stretch; flex-direction: column; }
  .metric-toolbar .search-input, .metric-toolbar .ed-select { width: 100%; }
  .two-columns, .three-columns { grid-template-columns: 1fr; }
}
</style>
