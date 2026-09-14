import type { Router } from 'vue-router'

const TRANSPORT_PREFIX = 'adaptive:rsa-oaep:v1:'

const pemToArrayBuffer = (pem: string) => {
  const base64 = pem.replace(/-----BEGIN PUBLIC KEY-----|-----END PUBLIC KEY-----|\s/g, '')
  const binary = atob(base64)
  return Uint8Array.from(binary, (char) => char.charCodeAt(0)).buffer
}

const bytesToBase64 = (bytes: Uint8Array) => {
  let binary = ''
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte)
  })
  return btoa(binary)
}

let publicKey: CryptoKey | undefined
let activeApiBaseUrl = ''

/** Community replacement for the former xpack browser license runtime. */
export const LicenseGenerator = {
  async init(apiBaseUrl = import.meta.env.VITE_API_BASE_URL) {
    if (publicKey && activeApiBaseUrl === apiBaseUrl) return true

    const response = await fetch(`${apiBaseUrl}/login/public-key`)
    if (!response.ok) throw new Error(`Unable to load Adaptive public key (${response.status})`)
    const payload = await response.json()
    const pem = payload?.data?.public_key ?? payload?.public_key
    if (!pem) throw new Error('Adaptive public key is missing')

    publicKey = await crypto.subtle.importKey(
      'spki',
      pemToArrayBuffer(pem),
      { name: 'RSA-OAEP', hash: 'SHA-256' },
      false,
      ['encrypt']
    )
    activeApiBaseUrl = apiBaseUrl
    return true
  },

  generateRouters(_router: Router) {
    // Enterprise-only routes are intentionally not injected.
  },

  getLicense() {
    return { status: 'community', edition: 'adaptive-community' }
  },

  async sqlbotEncrypt(value: string) {
    await this.init()
    const encrypted = await crypto.subtle.encrypt(
      { name: 'RSA-OAEP' },
      publicKey as CryptoKey,
      new TextEncoder().encode(value)
    )
    return `${TRANSPORT_PREFIX}${bytesToBase64(new Uint8Array(encrypted))}`
  },
}
