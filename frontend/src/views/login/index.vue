<template>
  <div
    v-if="showLoading"
    v-loading="true"
    :element-loading-text="t('qa.loading')"
    class="xpack-login-handler-mask"
    element-loading-background="#F5F6F7"
  ></div>

  <div
    ref="loginContainer"
    class="login-container"
    :class="{ 'hide-login-container': showLoading }"
  >
    <div v-if="showLoginImage" class="login-image-content">
      <el-image class="login-image" fit="cover" :src="bg" />
    </div>
    <div class="login-content">
      <div class="login-right">
        <div class="login-logo-icon">
          <AdaptiveLogo class="login-brand" />
        </div>
        <div v-if="appearanceStore.getShowSlogan" class="welcome">
          {{ appearanceStore.slogan ?? $t('common.intelligent_questioning_platform') }}
        </div>
        <div v-else class="welcome" style="height: 0"></div>
        <div class="login-form">
          <div class="default-login-tabs">
            <h2 class="title">{{ $t('common.login') }}</h2>
            <el-form
              ref="loginFormRef"
              class="form-content_error"
              :model="loginForm"
              :rules="rules"
              @keyup.enter="submitForm"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  clearable
                  :placeholder="$t('login.input_account')"
                  size="large"
                ></el-input>
              </el-form-item>
              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  :placeholder="$t('common.enter_your_password')"
                  type="password"
                  show-password
                  clearable
                  size="large"
                ></el-input>
              </el-form-item>
              <el-form-item>
                <el-button type="primary" class="login-btn" @click="submitForm">{{
                  $t('common.login_')
                }}</el-button>
              </el-form-item>
            </el-form>
          </div>
          <Handler
            v-model:loading="showLoading"
            jsname="L2NvbXBvbmVudC9sb2dpbi9IYW5kbGVy"
            @switch-tab="switchTab"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useI18n } from 'vue-i18n'
import AdaptiveLogo from '@/components/brand/AdaptiveLogo.vue'
import login_image from '@/assets/brand/adaptive-login.png'
import { useAppearanceStoreWithOut } from '@/stores/appearance'
import Handler from './xpack/Handler.vue'
import { toLoginSuccess } from '@/utils/utils'
import elementResizeDetectorMaker from 'element-resize-detector'

const showLoading = ref(true)
const router = useRouter()
const userStore = useUserStore()
const appearanceStore = useAppearanceStoreWithOut()
const { t } = useI18n()
const loginForm = ref({
  username: '',
  password: '',
})
const activeName = ref('simple')

// const isLdap = computed(() => activeName.value == 'ldap')
const bg = computed(() => {
  return login_image
})
const loginContainerWidth = ref(0)
const loginContainer = ref()
const showLoginImage = computed<boolean>(() => {
  return !(loginContainerWidth.value < 889)
})

onMounted(async () => {
  const erd = elementResizeDetectorMaker()
  erd.listenTo(loginContainer.value, () => {
    nextTick(() => {
      loginContainerWidth.value = loginContainer.value?.offsetWidth
    })
  })
})
const rules = {
  username: [{ required: true, message: t('common.your_account_email_address'), trigger: 'blur' }],
  password: [{ required: true, message: t('common.the_correct_password'), trigger: 'blur' }],
}

const loginFormRef = ref()

const submitForm = () => {
  loginFormRef.value.validate((valid: boolean) => {
    if (valid) {
      userStore.login(loginForm.value).then(() => {
        toLoginSuccess(router)
      })
    }
  })
}
const switchTab = (name: string) => {
  activeName.value = name || 'simple'
}
</script>

<style lang="less" scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
  display: flex;
  align-items: center;
  justify-content: center;

  .login-image-content {
    overflow: hidden;
    height: 100%;
    width: 40%;
    min-width: 400px;
    .login-image {
      background-size: 100% 100%;
      width: 100%;
      height: 100%;
      filter: saturate(0.92) contrast(1.02);
    }
  }

  .login-content {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;

    .login-right {
      display: flex;
      align-items: center;
      flex-direction: column;
      position: relative;

      .login-logo-icon {
        width: auto;
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: center;

        .login-brand {
          :deep(.adaptive-brand__mark) {
            width: 52px;
            height: 52px;
          }

          :deep(.adaptive-brand__wordmark) {
            font-size: 34px;
          }
        }
      }
      .welcome {
        margin: 8px 0 40px 0;
        font-weight: 400;
        font-size: 14px;
        line-height: 20px;
        color: #646a73;
      }

      .login-form {
        border: 1px solid #e0e7ff;
        padding: 40px;
        width: 480px;
        min-height: 392px;
        border-radius: 16px;
        box-shadow: 0 18px 48px rgba(30, 41, 100, 0.12);

        .form-content_error {
          .ed-form-item--default {
            margin-bottom: 24px;
            &.is-error {
              margin-bottom: 48px;
            }
          }
        }

        .title {
          font-weight: 500;
          font-style: Medium;
          font-size: 20px;
          line-height: 28px;
          margin-bottom: 24px;
        }

        .login-btn {
          width: 100%;
          height: 40px;
          font-size: 16px;
          border-radius: 6px;
        }

        .agreement {
          margin-top: 20px;
          text-align: center;
          color: #666;
        }
      }
    }
  }
}
.hide-login-container {
  display: none;
}

.xpack-login-handler-mask {
  position: fixed;
  width: 100vw;
  height: 100vh;
  left: 0;
  top: 0;
  z-index: 999;
}
</style>
