<script setup lang="ts">
import { type ChatMessage } from '@/api/chat.ts'
import { computed, onMounted, ref } from 'vue'
import MdComponent from '@/views/chat/component/MdComponent.vue'
import icon_up_outlined from '@/assets/svg/icon_up_outlined.svg'
import icon_down_outlined from '@/assets/svg/icon_down_outlined.svg'
import { useI18n } from 'vue-i18n'
import { useChatConfigStore } from '@/stores/chatConfig.ts'

const props = withDefaults(
  defineProps<{
    message: ChatMessage
    loading?: boolean
    reasoningName:
      | 'sql_answer'
      | 'chart_answer'
      | 'analysis_thinking'
      | 'predict'
      | Array<'sql_answer' | 'chart_answer' | 'analysis_thinking' | 'predict'>
  }>(),
  {
    loading: false,
  }
)

const { t } = useI18n()

const chatConfig = useChatConfigStore()

const show = ref<boolean>(false)

const reasoningContent = computed<Array<string>>(() => {
  const names: Array<'sql_answer' | 'chart_answer' | 'analysis_thinking' | 'predict'> = []
  if (typeof props.reasoningName === 'string') {
    names.push(props.reasoningName)
  } else {
    props.reasoningName.forEach((item) => {
      names.push(item)
    })
  }
  const result: Array<string> = []
  names.forEach((item) => {
    if (props.message?.record) {
      if (props.message?.record[item]) {
        result.push(props.message?.record[item] ?? '')
      }
    }
  })
  return result
})

const hasReasoning = computed<boolean>(() => {
  if (!chatConfig.getHideThinkingBlock) {
    if (reasoningContent.value.length > 0) {
      for (let i = 0; i < reasoningContent.value.length; i++) {
        if (reasoningContent.value[i] && reasoningContent.value[i].trim() !== '') {
          return true
        }
      }
    }
  }
  return false
})

function clickShow() {
  show.value = !show.value
}

onMounted(() => {
  if (props.message.isTyping) {
    // 根据配置项是否默认展开
    show.value = chatConfig.getExpandThinkingBlock
  }
})
</script>

<template>
  <div class="base-answer-block">
    <el-button v-if="message.isTyping || hasReasoning" class="thinking-btn" @click="clickShow">
      <div class="thinking-btn-inner">
        <span v-if="message.isTyping">{{ t('qa.thinking') }}</span>
        <span v-else>{{ t('qa.thinking_step') }}</span>
        <span class="btn-icon">
          <el-icon v-if="show">
            <icon_up_outlined />
          </el-icon>
          <el-icon v-else>
            <icon_down_outlined />
          </el-icon>
        </span>
      </div>
    </el-button>
    <div v-if="hasReasoning && show" class="reasoning-content flex-gap-fallback flex-col">
      <div v-for="(reason, _index) in reasoningContent" :key="_index" class="reasoning">
        <MdComponent :message="reason" />
      </div>
    </div>
    <div class="answer-container">
      <slot></slot>
      <el-button v-if="message.isTyping" style="min-width: unset" type="primary" link loading />
      <slot name="tool"></slot>
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<style scoped lang="less">
.base-answer-block {
  .thinking-btn {
    height: 32px;
    padding: 5px 12px;
    border-radius: 8px;

    --ed-button-text-color: #315f96;
    --ed-button-hover-text-color: #125fc2;
    --ed-button-active-text-color: #0d4fa6;
    --ed-button-bg-color: rgba(235, 244, 255, 0.88);
    --ed-button-hover-bg-color: #e1efff;
    --ed-button-active-bg-color: #d7e9ff;
    --ed-button-border-color: #c9ddf6;
    --ed-button-hover-border-color: #9fc5f2;
    --ed-button-active-border-color: #7fb0e9;

    --ed-button-font-weight: 400;

    .thinking-btn-inner {
      display: flex;
      flex-direction: row;
      align-items: center;

      line-height: 22px;
      font-weight: 400;
      font-size: 14px;
    }
    .btn-icon {
      margin-left: 4px;
    }
  }

  .reasoning-content {
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    padding: 12px 14px 12px 16px;
    border: 1px solid #d8e7f8;
    border-radius: 10px;
    background: linear-gradient(135deg, rgba(246, 250, 255, 0.96), rgba(237, 245, 255, 0.92));
    box-shadow: inset 3px 0 0 #6ca7e8, 0 4px 14px rgba(45, 94, 153, 0.06);
    --gap-size: 8px;
    gap: 8px;

    .reasoning {
      width: 100%;
      line-height: 22px;
      font-weight: 400;
      font-size: 14px;
      color: #5f7188 !important;

      :deep(.markdown-body) {
        color: #5f7188 !important;
        background: transparent !important;
        line-height: 22px;
        font-weight: 400;
        font-size: 14px;

        pre,
        code {
          background-color: rgba(218, 233, 251, 0.68) !important;
        }
      }

      padding-bottom: 8px;
      border-bottom: 1px solid rgba(87, 132, 185, 0.16);

      &:last-child {
        padding-bottom: unset;
        border-bottom: unset;
      }
    }
  }

  .answer-container {
    width: 100%;

    line-height: 24px;
    font-size: 16px;
    font-weight: 400;
    color: rgba(31, 35, 41, 1);
  }
}
</style>
