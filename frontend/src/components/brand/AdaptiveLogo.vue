<script setup lang="ts">
withDefaults(
  defineProps<{
    compact?: boolean
    inverse?: boolean
  }>(),
  {
    compact: false,
    inverse: false,
  }
)
</script>

<template>
  <div class="adaptive-brand" :class="{ compact, inverse }" aria-label="一言SQL">
    <img class="adaptive-brand__mark" src="@/assets/brand/adaptive-mark.png" alt="" />
    <div v-if="!compact" class="adaptive-brand__wordmark">
      <span>一言</span>
      <small>SQL</small>
    </div>
  </div>
</template>

<style scoped lang="less">
.adaptive-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #172554;

  &__mark {
    width: 34px;
    height: 34px;
    object-fit: contain;
  }

  &__wordmark {
    display: flex;
    align-items: baseline;
    gap: 6px;
    font-size: 21px;
    font-weight: 760;
    letter-spacing: -0.6px;

    small {
      color: #0f766e;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 1.4px;
    }
  }

  &.compact {
    gap: 0;
  }

  &.inverse {
    color: #ffffff;
  }
}
</style>
