<script lang="ts" setup>
import { ref, computed, onUnmounted } from 'vue'
import Menu from './Menu.vue'
import Workspace from './Workspace.vue'
import Person from './Person.vue'
import AdaptiveLogo from '@/components/brand/AdaptiveLogo.vue'
import icon_moments_categories_outlined from '@/assets/svg/icon_moments-categories_outlined.svg'
import icon_side_fold_outlined from '@/assets/svg/icon_side-fold_outlined.svg'
import icon_side_expand_outlined from '@/assets/svg/icon_side-expand_outlined.svg'
import { useRoute, useRouter } from 'vue-router'
import { useEmitt } from '@/utils/useEmitt'
import { isMobile } from '@/utils/utils'
import { onBeforeMount } from 'vue'

const isPhone = computed(() => {
  return isMobile()
})
const router = useRouter()
const collapse = ref(false)
const collapseCopy = ref(false)
let time: any
onUnmounted(() => {
  clearTimeout(time)
})
const handleCollapseChange = (val: any = true) => {
  collapseCopy.value = val
  clearTimeout(time)
  time = setTimeout(() => {
    collapse.value = val
  }, 100)
}
useEmitt({
  name: 'collapse-change',
  callback: handleCollapseChange,
})
const handleFoldExpand = () => {
  handleCollapseChange(!collapse.value)
}

const toWorkspace = () => {
  router.push('/')
}

const toChatIndex = () => {
  router.push('/chat/index')
}

const toUserIndex = () => {
  router.push('/system/user')
}
const route = useRoute()
const showSysmenu = computed(() => {
  return route.path.includes('/system')
})
onBeforeMount(() => {
  if (isPhone.value) {
    collapse.value = true
    collapseCopy.value = true
  }
})
</script>

<template>
  <div class="system-layout">
    <div class="left-side" :class="collapse && 'left-side-collapse'">
      <template v-if="showSysmenu">
        <div class="sys-management" @click="toUserIndex">
          <AdaptiveLogo :compact="collapse" :class="!collapse && 'collapse-icon'" />
          <span v-if="!collapse">{{ $t('training.system_management') }}</span>
        </div>
      </template>
      <template v-else>
        <div class="default-sqlbot" @click="toChatIndex">
          <AdaptiveLogo :compact="collapse" />
        </div>
      </template>
      <Workspace v-if="!showSysmenu" :collapse="collapse"></Workspace>
      <Menu :collapse="collapseCopy"></Menu>
      <div class="bottom">
        <div
          v-if="showSysmenu"
          class="back-to_workspace"
          :class="collapse && 'collapse'"
          @click="toWorkspace"
        >
          <el-icon size="18">
            <icon_moments_categories_outlined></icon_moments_categories_outlined>
          </el-icon>
          {{ collapse ? '' : $t('workspace.return_to_workspace') }}
        </div>
        <div class="personal-info">
          <Person :collapse="collapse" :in-sysmenu="showSysmenu"></Person>
          <el-icon size="20" class="fold" @click="handleFoldExpand">
            <icon_side_expand_outlined v-if="collapse"></icon_side_expand_outlined>
            <icon_side_fold_outlined v-else></icon_side_fold_outlined>
          </el-icon>
        </div>
      </div>
    </div>
    <div class="right-main" :class="collapse && 'right-side-collapse'">
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<style lang="less" scoped>
.system-layout {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(145deg, #d9e8fb 0%, #eaf3ff 52%, #dcecff 100%);
  display: flex;

  @keyframes rotate {
    0% {
      width: 240px;
    }
    100% {
      width: 64px;
    }
  }

  .left-side {
    width: 240px;
    height: 100%;
    padding: 16px;
    position: relative;
    min-width: 240px;
    color: #173b6c;
    background: linear-gradient(180deg, #eef6ff 0%, #dceaff 100%);
    box-shadow: 8px 0 28px rgba(35, 86, 150, 0.1);

    :deep(.adaptive-brand) {
      color: #163b70;

      .adaptive-brand__wordmark small {
        color: #087ea4;
      }
    }

    :deep(.workspace) {
      color: #244d7c;
      background: rgba(255, 255, 255, 0.7);
      border-color: #bed4f2;

      &:hover,
      &:active {
        background: #ffffff;
      }
    }

    :deep(.ed-menu-vertical) {
      --ed-menu-text-color: #31547d;
      --ed-menu-hover-text-color: #125fc2;
      --ed-menu-active-color: #ffffff;
      --ed-menu-hover-bg-color: rgba(22, 119, 255, 0.08);

      .ed-menu-item,
      .ed-sub-menu__title {
        color: #31547d !important;

        .ed-icon,
        svg {
          color: currentColor !important;
        }
      }

      .ed-menu-item:hover,
      .ed-sub-menu__title:hover {
        color: #125fc2 !important;
        background: rgba(22, 119, 255, 0.08) !important;
      }

      .ed-menu-item.is-active,
      .ed-sub-menu.is-active:not(.is-opened) .ed-sub-menu__title {
        color: #ffffff !important;
        background: linear-gradient(90deg, #1677ff, #2b8cff) !important;
        box-shadow: 0 6px 16px rgba(22, 119, 255, 0.2);
      }

      .ed-sub-menu.is-active.is-opened > .ed-sub-menu__title {
        color: #31547d !important;
        background: transparent !important;
        box-shadow: none;
      }
    }

    :deep(.person) {
      color: #244d7c;
    }

    .fold {
      color: #31547d;
    }

    .default-sqlbot {
      display: flex;
      align-items: center;
      font-weight: 500;
      font-size: 16px;
      cursor: pointer;
      margin-bottom: 12px;
      .collapse-icon {
        margin-right: 8px;
      }
    }

    .sys-management {
      display: flex;
      align-items: center;
      font-weight: 500;
      font-size: 16px;
      cursor: pointer;
      margin-bottom: 12px;
      .collapse-icon {
        margin-right: 8px;
      }
    }

    .bottom {
      position: absolute;
      bottom: 20px;
      left: 16px;
      font-weight: 400;
      font-size: 14px;
      line-height: 22px;
      width: calc(100% - 32px);
      .back-to_workspace {
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        height: 40px;
        cursor: pointer;

        &:not(.collapse) {
          background: rgba(255, 255, 255, 0.7);
          border: 1px solid #bed4f2;
        }
        &:hover {
          background-color: #ffffff;
        }
        &:active {
          background-color: #d3e6ff;
        }
        .ed-icon {
          margin-right: 4.95px;
        }
      }

      .personal-info {
        display: flex;
        align-items: center;
        margin-top: 16px;

        .fold {
          cursor: pointer;
          margin-left: auto;
          border-radius: 6px;
          width: 40px;
          height: 40px;
          &:hover,
          &:focus {
            background: rgba(22, 119, 255, 0.09);
          }

          &:active {
            background: rgba(22, 119, 255, 0.15);
          }
        }
      }
    }

    &.left-side-collapse {
      width: 64px;
      min-width: 64px;
      padding: 16px 12px;
      // animation: rotate 0.1s ease-in-out;

      .ed-menu--collapse {
        --ed-menu-icon-width: 32px;
        width: 40px;
      }

      .bottom {
        left: 12px;
        width: calc(100% - 24px);
        .ed-icon {
          margin-right: 0;
        }
      }

      .personal-info {
        flex-wrap: wrap;

        .default-avatar {
          margin: 0 0 26px 4px;
        }

        .fold {
          margin: 0 auto;
        }
      }
    }
  }

  .right-main {
    width: calc(100% - 240px);
    padding: 0;
    max-height: 100vh;

    &.right-side-collapse {
      width: calc(100% - 64px);
    }

    .content {
      width: 100%;
      height: 100%;
      padding: 16px 24px;
      background: linear-gradient(145deg, #fbfdff 0%, #f3f8ff 100%);
      border-radius: 0;
      box-shadow: -6px 0 24px rgba(38, 83, 139, 0.08);
      overflow-x: auto;

      &:has(.no-padding) {
        padding: 0;
      }
    }
  }
}
</style>
