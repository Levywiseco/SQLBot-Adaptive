<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { type ChatLogHistoryItem } from '@/api/chat.ts'
import BaseContent from './BaseContent.vue'

const props = withDefaults(
  defineProps<{ item?: ChatLogHistoryItem; error?: string }>(),
  { item: undefined, error: '' }
)
const { t } = useI18n()
const list = computed(() => (props.item?.message as Array<any>) ?? [])
</script>

<template>
  <BaseContent>
    <template v-if="item?.error">{{ error }}</template>
    <template v-else>
      <div class="summary">{{ t('chat.find_memory_title', [list.length]) }}</div>
      <div v-if="list.length" class="memory-list">
        <div v-for="memory in list" :key="`${memory.id}-${memory.version}`" class="memory-card">
          <div class="memory-title">
            <strong>{{ memory.title }}</strong>
            <el-tag size="small" :type="memory.scope === 'personal' ? 'success' : 'info'">
              {{ t(`memory.scope_${memory.scope}`) }}
            </el-tag>
            <span>v{{ memory.version }}</span>
          </div>
          <div class="memory-meta">{{ t(`memory.type_${memory.memory_type}`) }} · {{ t(`memory.source_${memory.source_type}`) }}</div>
        </div>
      </div>
    </template>
  </BaseContent>
</template>

<style scoped lang="less">
.summary, .memory-meta { color: #646a73; font-size: 12px; line-height: 20px; }
.memory-list { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.memory-card { padding: 14px 16px; border: 1px solid #dee0e3; border-radius: 12px; background: #fff; }
.memory-title { display: flex; align-items: center; gap: 8px; }
.memory-title span { color: #8f959e; font-size: 12px; }
.memory-meta { margin-top: 6px; }
</style>
