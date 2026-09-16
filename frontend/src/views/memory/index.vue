<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus-secondary'
import { memoryApi, type MemoryPayload } from '@/api/adaptive'
import { datasourceApi } from '@/api/datasource'
import { formatTimestamp } from '@/utils/date'
import EmptyBackground from '@/views/dashboard/common/EmptyBackground.vue'
import icon_add_outlined from '@/assets/svg/icon_add_outlined.svg'
import icon_searchOutline_outlined from '@/assets/svg/icon_search-outline_outlined.svg'
import IconOpeEdit from '@/assets/svg/icon_edit_outlined.svg'
import IconOpeDelete from '@/assets/svg/icon_delete.svg'

interface MemoryForm extends MemoryPayload {
  id?: number | null
  keywords_text: string
}

const { t } = useI18n()
const loading = ref(false)
const saving = ref(false)
const rows = ref<any[]>([])
const datasources = ref<any[]>([])
const keyword = ref('')
const statusFilter = ref('')
const datasourceFilter = ref<number>()
const editVisible = ref(false)
const formRef = ref()
const pageInfo = reactive({ currentPage: 1, pageSize: 10, total: 0 })

const emptyForm = (): MemoryForm => ({
  id: null,
  title: '',
  content: '',
  memory_type: 'preference',
  scope: 'personal',
  keywords: [],
  keywords_text: '',
  datasource_id: null,
  expires_at: null,
  priority: 0,
})
const form = ref<MemoryForm>(emptyForm())
const drawerTitle = computed(() =>
  form.value.id ? t('memory.edit_memory') : t('memory.create_memory')
)
const rules = {
  title: [{ required: true, message: t('memory.title_required'), trigger: 'blur' }],
  content: [{ required: true, message: t('memory.content_required'), trigger: 'blur' }],
}

const splitList = (value: string) =>
  [...new Set(value.split(/[,，\n]/).map((item) => item.trim()).filter(Boolean))]

const load = async () => {
  loading.value = true
  try {
    const result = await memoryApi.page(pageInfo.currentPage, pageInfo.pageSize, {
      keyword: keyword.value || undefined,
      status: statusFilter.value || undefined,
      datasource_id: datasourceFilter.value,
      scope: 'personal',
    })
    rows.value = result.data || []
    pageInfo.total = result.total_count || 0
  } finally {
    loading.value = false
  }
}

const resetAndLoad = () => {
  pageInfo.currentPage = 1
  load()
}

const openCreate = () => {
  form.value = emptyForm()
  editVisible.value = true
}

const openEdit = (row: any) => {
  form.value = {
    id: row.id,
    title: row.title || '',
    content: row.content || '',
    memory_type: row.memory_type || 'preference',
    scope: 'personal',
    keywords: row.keywords || [],
    keywords_text: (row.keywords || []).join(', '),
    datasource_id: row.datasource_id || null,
    expires_at: row.expires_at || null,
    priority: row.priority || 0,
  }
  editVisible.value = true
}

const save = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload: MemoryPayload = {
      title: form.value.title.trim(),
      content: form.value.content.trim(),
      memory_type: 'preference',
      scope: 'personal',
      keywords: splitList(form.value.keywords_text),
      datasource_id: form.value.datasource_id || null,
      expires_at: form.value.expires_at || null,
      priority: form.value.priority || 0,
    }
    if (form.value.id) await memoryApi.update(form.value.id, payload)
    else await memoryApi.create(payload)
    ElMessage.success(t('common.save_success'))
    editVisible.value = false
    await load()
  } finally {
    saving.value = false
  }
}

const toggleStatus = async (row: any) => {
  await memoryApi.status(row.id, row.status === 'active' ? 'paused' : 'active')
  ElMessage.success(t('memory.status_changed'))
  await load()
}

const remove = async (row: any) => {
  await ElMessageBox.confirm(t('memory.delete_confirm', { name: row.title }), {
    confirmButtonText: t('common.delete'),
    cancelButtonText: t('common.cancel'),
    confirmButtonType: 'danger',
  })
  await memoryApi.remove(row.id)
  ElMessage.success(t('memory.deleted'))
  await load()
}

onMounted(async () => {
  datasources.value = (await datasourceApi.list()) || []
  await load()
})
</script>

<template>
  <div v-loading="loading" class="memory-page">
    <section class="memory-heading">
      <div>
        <h1>{{ t('memory.my_memory') }}</h1>
        <p>{{ t('memory.description') }}</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <template #icon><icon_add_outlined /></template>
        {{ t('memory.create_memory') }}
      </el-button>
    </section>

    <el-alert class="memory-rule" :title="t('memory.priority_rule')" type="info" show-icon :closable="false" />

    <section class="memory-toolbar">
      <el-input
        v-model="keyword"
        clearable
        class="search-input"
        :placeholder="t('memory.search_placeholder')"
        @keyup.enter="resetAndLoad"
        @clear="resetAndLoad"
      >
        <template #prefix><el-icon><icon_searchOutline_outlined /></el-icon></template>
      </el-input>
      <el-select v-model="datasourceFilter" clearable :placeholder="t('memory.all_datasources')" @change="resetAndLoad">
        <el-option v-for="item in datasources" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="statusFilter" clearable :placeholder="t('memory.all_statuses')" @change="resetAndLoad">
        <el-option :label="t('memory.status_active')" value="active" />
        <el-option :label="t('memory.status_paused')" value="paused" />
      </el-select>
      <el-button secondary @click="resetAndLoad">{{ t('common.search') }}</el-button>
    </section>

    <section class="memory-table">
      <el-table :data="rows" @row-dblclick="openEdit">
        <el-table-column prop="title" :label="t('memory.title')" min-width="160">
          <template #default="scope">
            <div class="memory-title">{{ scope.row.title }}</div>
            <div class="muted">v{{ scope.row.version }} · {{ t(`memory.type_${scope.row.memory_type}`) }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="content" :label="t('memory.content')" min-width="240" show-overflow-tooltip />
        <el-table-column prop="datasource_name" :label="t('memory.datasource')" min-width="145">
          <template #default="scope">{{ scope.row.datasource_name || t('memory.all_datasources') }}</template>
        </el-table-column>
        <el-table-column :label="t('memory.source')" width="120">
          <template #default="scope">{{ t(`memory.source_${scope.row.source_type}`) }}</template>
        </el-table-column>
        <el-table-column :label="t('memory.status')" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
              {{ t(`memory.status_${scope.row.status}`) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('memory.updated_at')" width="145">
          <template #default="scope">{{ formatTimestamp(scope.row.updated_at, 'YYYY-MM-DD HH:mm:ss') }}</template>
        </el-table-column>
        <el-table-column fixed="right" :label="t('ds.actions')" width="175">
          <template #default="scope">
            <div class="row-actions">
              <el-button link type="primary" @click.stop="toggleStatus(scope.row)">
                {{ scope.row.status === 'active' ? t('memory.pause') : t('memory.activate') }}
              </el-button>
              <el-tooltip :content="t('datasource.edit')" placement="top">
                <el-icon class="action-icon" @click.stop="openEdit(scope.row)"><IconOpeEdit /></el-icon>
              </el-tooltip>
              <el-tooltip :content="t('common.delete')" placement="top">
                <el-icon class="action-icon" @click.stop="remove(scope.row)"><IconOpeDelete /></el-icon>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        <template #empty><EmptyBackground :description="t('memory.empty')" img-type="noneWhite" /></template>
      </el-table>
    </section>

    <div v-if="pageInfo.total" class="pagination-container">
      <el-pagination
        v-model:current-page="pageInfo.currentPage"
        v-model:page-size="pageInfo.pageSize"
        :page-sizes="[10, 20, 30]"
        background
        layout="total, sizes, prev, pager, next"
        :total="pageInfo.total"
        @size-change="load"
        @current-change="load"
      />
    </div>
  </div>

  <el-drawer v-model="editVisible" :title="drawerTitle" size="620px" destroy-on-close>
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item prop="title" :label="t('memory.title')"><el-input v-model="form.title" maxlength="255" /></el-form-item>
      <el-form-item prop="content" :label="t('memory.content')">
        <el-input v-model="form.content" type="textarea" :rows="7" maxlength="4000" show-word-limit />
        <div class="field-hint">{{ t('memory.content_hint') }}</div>
      </el-form-item>
      <el-form-item :label="t('memory.keywords')">
        <el-input v-model="form.keywords_text" :placeholder="t('memory.keywords_hint')" />
      </el-form-item>
      <div class="form-grid">
        <el-form-item :label="t('memory.datasource')">
          <el-select v-model="form.datasource_id" clearable :placeholder="t('memory.all_datasources')">
            <el-option v-for="item in datasources" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('memory.expires_at')">
          <el-date-picker v-model="form.expires_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" clearable />
        </el-form-item>
      </div>
    </el-form>
    <template #footer>
      <el-button secondary @click="editVisible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="saving" @click="save">{{ t('common.save') }}</el-button>
    </template>
  </el-drawer>
</template>

<style lang="less" scoped>
.memory-page { height: 100%; padding: 24px; background: #f7f8fa; overflow: auto; }
.memory-heading, .memory-toolbar, .row-actions { display: flex; align-items: center; }
.memory-heading { justify-content: space-between; margin-bottom: 16px; }
.memory-heading h1 { margin: 0 0 6px; font-size: 24px; color: #1f2329; }
.memory-heading p { margin: 0; color: #646a73; font-size: 14px; }
.memory-rule { margin-bottom: 16px; }
.memory-toolbar { gap: 12px; padding: 16px; background: #fff; border: 1px solid #e5e6eb; border-bottom: 0; border-radius: 10px 10px 0 0; }
.memory-toolbar .search-input { width: 280px; }
.memory-toolbar .ed-select { width: 190px; }
.memory-table { background: #fff; border: 1px solid #e5e6eb; border-radius: 0 0 10px 10px; overflow: hidden; }
.memory-title { font-weight: 500; color: #1f2329; }
.muted, .field-hint { color: #73849a; font-size: 12px; margin-top: 4px; }
.row-actions { gap: 10px; }
.action-icon { cursor: pointer; color: #646a73; }
.action-icon:hover { color: var(--ed-color-primary); }
.pagination-container { display: flex; justify-content: flex-end; padding: 16px 0; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
:deep(.ed-select), :deep(.ed-date-editor) { width: 100%; }
@media (max-width: 900px) {
  .memory-heading, .memory-toolbar { align-items: stretch; flex-direction: column; }
  .memory-toolbar .search-input, .memory-toolbar .ed-select { width: 100%; }
  .form-grid { grid-template-columns: 1fr; }
}
</style>
