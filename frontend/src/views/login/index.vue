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
  background: linear-gradient(135deg, #dcecff 0%, #edf6ff 52%, #d5e8ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;

  .login-image-content {
    overflow: hidden;
    height: 100%;
    width: 40%;
    min-width: 400px;
    position: relative;

    &::after {
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(90deg, rgba(7, 52, 111, 0.04), rgba(38, 111, 194, 0.14));
      pointer-events: none;
    }
    .login-image {
      background-size: 100% 100%;
      width: 100%;
      height: 100%;
      filter: saturate(0.92) contrast(1.02);
    }
  }

  .login-content {
    position: relative;
    height: 100%;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    background:
      radial-gradient(circle at 84% 16%, rgba(68, 151, 245, 0.2), transparent 30%),
      radial-gradient(circle at 12% 88%, rgba(91, 180, 255, 0.14), transparent 28%),
      linear-gradient(145deg, #f1f7ff 0%, #e5f1ff 52%, #dcecff 100%);

    &::before,
    &::after {
      content: '';
      position: absolute;
      border: 1px solid rgba(55, 128, 217, 0.12);
      border-radius: 50%;
      pointer-events: none;
    }

    &::before {
      width: 420px;
      height: 420px;
      top: -220px;
      right: -110px;
    }

    &::after {
      width: 280px;
      height: 280px;
      right: 12%;
      bottom: -190px;
    }

    .login-right {
      display: flex;
      align-items: center;
      flex-direction: column;
      position: relative;
      z-index: 1;
      width: 100%;

      .login-logo-icon {
        width: auto;
        height: 52px;
        display: flex;
        align-items: center;
        justify-content: center;

        .login-brand {
          color: #163b70;

          :deep(.adaptive-brand__mark) {
            width: 52px;
            height: 52px;
          }

          :deep(.adaptive-brand__wordmark) {
            font-size: 34px;
            color: #163b70;

            small {
              color: #087ea4;
            }
          }
        }
      }
      .welcome {
        margin: 10px 0 28px;
        font-weight: 400;
        font-size: 14px;
        line-height: 20px;
        color: #58749b;
      }

      .login-form {
        border: 1px solid rgba(170, 201, 237, 0.62);
        padding: 34px 40px 32px;
        width: 440px;
        min-height: 300px;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.94);
        box-shadow:
          0 24px 64px rgba(38, 84, 139, 0.16),
          0 3px 12px rgba(38, 84, 139, 0.06);
        backdrop-filter: blur(20px);

        :deep(.ed-input__wrapper) {
          min-height: 44px;
          border-radius: 10px;
          box-shadow: 0 0 0 1px #d5e1ef inset;
          transition: box-shadow 0.2s ease;
        }

        :deep(.ed-input__wrapper.is-focus) {
          box-shadow: 0 0 0 1px #337dcc inset, 0 0 0 3px rgba(51, 125, 204, 0.1);
        }

        .form-content_error {
          .ed-form-item--default {
            margin-bottom: 24px;
            &.is-error {
              margin-bottom: 48px;
            }
          }
        }

        .title {
          font-weight: 650;
          font-size: 20px;
          line-height: 28px;
          margin-bottom: 24px;
          color: #173b68;
        }

        .login-btn {
          width: 100%;
          height: 44px;
          font-size: 16px;
          font-weight: 600;
          border: 0;
          border-radius: 10px;
          background: linear-gradient(90deg, #2268b8, #398bd7);
          box-shadow: 0 8px 18px rgba(36, 105, 184, 0.24);
          transition: transform 0.2s ease, box-shadow 0.2s ease;

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 22px rgba(36, 105, 184, 0.3);
          }
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

@media (max-width: 960px) {
  .login-container {
    .login-image-content {
      display: none;
    }

    .login-content {
      width: 100%;
      padding: 24px;

      .login-right {
        .login-form {
          width: min(440px, calc(100vw - 48px));
          padding: 30px 28px 28px;
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
