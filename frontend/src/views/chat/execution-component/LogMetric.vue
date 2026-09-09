<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { type ChatLogHistoryItem } from '@/api/chat.ts'
import BaseContent from './BaseContent.vue'

const props = withDefaults(
  defineProps<{
    item?: ChatLogHistoryItem
    error?: string
  }>(),
  { item: undefined, error: '' }
)

const { t } = useI18n()
const list = computed(() => (props.item?.message as Array<any>) ?? [])
</script>

<template>
  <BaseContent class="metric-log">
    <template v-if="item?.error">{{ error }}</template>
    <template v-else>
      <div class="summary">{{ t('chat.find_metric_title', [list.length]) }}</div>
      <div v-if="list.length" class="metric-list">
        <div v-for="metric in list" :key="`${metric.id}-${metric.version}`" class="metric-card">
          <div class="metric-title">
            <strong>{{ metric.name }}</strong>
            <code>{{ metric.code }}</code>
            <el-tag size="small" type="success">v{{ metric.version }}</el-tag>
            <el-tag v-if="metric.inherited" size="small" type="info">{{ t('metric.inherited') }}</el-tag>
          </div>
          <p v-if="metric.description">{{ metric.description }}</p>
          <div v-if="metric.required_tables?.length" class="metric-tables">
            {{ t('metric.required_tables') }}：{{ metric.required_tables.join(', ') }}
          </div>
        </div>
      </div>
    </template>
  </BaseContent>
</template>

<style scoped lang="less">
.summary { color: #646a73; font-size: 12px; line-height: 20px; }
.metric-list { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.metric-card { padding: 14px 16px; border: 1px solid #dee0e3; border-radius: 12px; background: #fff; }
.metric-title { display: flex; align-items: center; gap: 8px; }
.metric-title code { color: #8f959e; font-size: 12px; }
.metric-card p { margin: 8px 0 0; color: #646a73; line-height: 20px; }
.metric-tables { margin-top: 8px; color: #8f959e; font-size: 12px; }
</style>
