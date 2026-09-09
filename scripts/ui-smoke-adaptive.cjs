const path = require('node:path')

const dependencyRoot =
  process.env.CODEX_DEPENDENCY_ROOT ||
  'C:\\Users\\yuyinghao\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node'
const { chromium } = require(path.join(dependencyRoot, 'node_modules', 'playwright'))

const root = path.resolve(__dirname, '..')
const baseUrl = process.env.SQLBOT_UI_URL || 'http://127.0.0.1:5173'
const edgePath =
  process.env.SQLBOT_BROWSER_PATH ||
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const username = process.env.SQLBOT_UI_USERNAME || 'admin'
const password = process.env.SQLBOT_UI_PASSWORD || 'SQLBot@123456'

async function main() {
  const browser = await chromium.launch({ executablePath: edgePath, headless: true })
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })
  const consoleErrors = []
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text())
  })

  try {
    await page.goto(`${baseUrl}/#/login`, { waitUntil: 'domcontentloaded' })
    const inputs = page.locator('input')
    await inputs.nth(0).fill(username)
    await inputs.nth(1).fill(password)
    await page.locator('.login-btn').click()
    await page.waitForURL((url) => !url.hash.includes('/login'), { timeout: 30_000 })

    await page.goto(`${baseUrl}/#/memory/index`, { waitUntil: 'domcontentloaded' })
    await page.getByText('我的记忆', { exact: true }).first().waitFor({ timeout: 20_000 })
    await page.getByText('金额展示单位', { exact: true }).waitFor({ timeout: 20_000 })
    await page.screenshot({
      path: path.join(root, 'docs', 'adaptive', 'memory-catalog-smoke.png'),
      fullPage: true,
    })

    await page.getByRole('button', { name: '新建记忆' }).click()
    await page.getByText('编辑记忆', { exact: true }).or(page.getByText('新建记忆', { exact: true })).first().waitFor()
    await page.keyboard.press('Escape')

    await page.goto(`${baseUrl}/#/set/learning`, { waitUntil: 'domcontentloaded' })
    await page.getByText('学习中心', { exact: true }).first().waitFor({ timeout: 20_000 })
    await page.getByText('净销售额必须排除未支付订单，并按支付日期归属月份', { exact: true }).waitFor({ timeout: 20_000 })
    await page.screenshot({
      path: path.join(root, 'docs', 'adaptive', 'learning-center-smoke.png'),
      fullPage: true,
    })

    await page.goto(`${baseUrl}/#/chat/index`, { waitUntil: 'domcontentloaded' })
    const demoChat = page.getByText('Adaptive learning demo (synthetic)', { exact: true })
    await demoChat.waitFor({ timeout: 20_000 })
    await demoChat.click()
    await page.getByText('记住', { exact: true }).waitFor({ timeout: 20_000 })
    await page.screenshot({
      path: path.join(root, 'docs', 'adaptive', 'feedback-controls-smoke.png'),
      fullPage: true,
    })

    const meaningfulErrors = consoleErrors.filter(
      (message) => !message.includes('404') && !message.includes('favicon')
    )
    if (meaningfulErrors.length) {
      throw new Error(`Browser console errors: ${meaningfulErrors.join(' | ')}`)
    }
    console.log('Adaptive UI smoke test passed: My Memory, Learning Center, and feedback controls')
  } finally {
    await browser.close()
  }
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
