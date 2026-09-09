<script lang="ts" setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Check, CollectionTag, Warning } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus-secondary'
import { feedbackApi, type FeedbackPayload } from '@/api/adaptive'

const props = defineProps<{
  recordId?: number
  disabled?: boolean
}>()

const { t } = useI18n()
const submitting = ref(false)
const submitted = ref('')

const idempotencyKey = (kind: string) => {
  const random = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`
  return `ui-${props.recordId}-${kind}-${random}`
}

const send = async (payload: Omit<FeedbackPayload, 'chat_record_id' | 'idempotency_key'>) => {
  if (!props.recordId || submitting.value) return
  submitting.value = true
  try {
    await feedbackApi.create({
      ...payload,
      chat_record_id: props.recordId,
      idempotency_key: idempotencyKey(payload.feedback_type),
    })
    submitted.value = payload.feedback_type
    ElMessage.success(
      payload.feedback_type === 'remember_preference'
        ? t('feedback.remembered')
        : t('feedback.recorded')
    )
  } finally {
    submitting.value = false
  }
}

const markCorrect = () => send({ feedback_type: 'correct' })

const submitWithDetail = async (
  type: 'result_wrong' | 'metric_wrong' | 'save_example'
) => {
  const result = await ElMessageBox.prompt(
    t(`feedback.${type}_hint`),
    t(`feedback.${type}`),
    {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      inputType: 'textarea',
      inputValidator: (value: string) =>
        value.trim().length >= 3 || t('feedback.detail_required'),
    }
  ).catch(() => null)
  if (!result) return
  await send({ feedback_type: type, correction_text: result.value.trim() })
}

const rememberPreference = async () => {
  const result = await ElMessageBox.prompt(
    t('feedback.remember_preference_hint'),
    t('feedback.remember_preference'),
    {
      confirmButtonText: t('feedback.remember'),
      cancelButtonText: t('common.cancel'),
      inputType: 'textarea',
      inputValidator: (value: string) =>
        value.trim().length >= 2 || t('feedback.preference_required'),
    }
  ).catch(() => null)
  if (!result) return
  const content = result.value.trim()
  await send({
    feedback_type: 'remember_preference',
    memory_title: content.slice(0, 40),
    memory_content: content,
  })
}
</script>

<template>
  <div class="feedback-controls">
    <el-tooltip :content="t('feedback.correct')" placement="top">
      <el-button
        class="feedback-btn"
        text
        :type="submitted === 'correct' ? 'success' : ''"
        :disabled="disabled || submitting || !recordId"
        @click="markCorrect"
      >
        <el-icon size="17"><Check /></el-icon>
      </el-button>
    </el-tooltip>
    <el-dropdown
      trigger="click"
      :disabled="disabled || submitting || !recordId"
      @command="submitWithDetail"
    >
      <el-button class="feedback-btn" text :type="submitted.includes('wrong') ? 'danger' : ''">
        <el-icon size="17"><Warning /></el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="result_wrong">{{ t('feedback.result_wrong') }}</el-dropdown-item>
          <el-dropdown-item command="metric_wrong">{{ t('feedback.metric_wrong') }}</el-dropdown-item>
          <el-dropdown-item command="save_example">{{ t('feedback.save_example') }}</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
    <el-tooltip :content="t('feedback.remember_preference')" placement="top">
      <el-button
        class="feedback-btn remember-btn"
        text
        :type="submitted === 'remember_preference' ? 'success' : ''"
        :disabled="disabled || submitting || !recordId"
        @click="rememberPreference"
      >
        <el-icon size="17"><CollectionTag /></el-icon>
        <span>{{ t('feedback.remember') }}</span>
      </el-button>
    </el-tooltip>
  </div>
</template>

<style lang="less" scoped>
.feedback-controls { display: inline-flex; align-items: center; gap: 2px; }
.feedback-btn { padding: 4px 6px; height: 28px; }
.remember-btn { gap: 4px; }
</style>
