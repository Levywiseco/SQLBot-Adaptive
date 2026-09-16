const path = require('node:path')

const dependencyRoot =
  process.env.CODEX_DEPENDENCY_ROOT ||
  'C:\\Users\\wangbing\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\node'
const { chromium } = require(path.join(dependencyRoot, 'node_modules', 'playwright'))

const root = path.resolve(__dirname, '..')
const baseUrl = process.env.ADAPTIVE_UI_URL || 'http://127.0.0.1:5180'
const edgePath =
  process.env.ADAPTIVE_BROWSER_PATH ||
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'

async function main() {
  const browser = await chromium.launch({ executablePath: edgePath, headless: true })
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
    locale: 'en-US',
  })
  const apiFailures = []
  page.on('pageerror', (error) => console.error(`Browser page error: ${error.stack || error}`))
  page.on('console', (message) => {
    if (message.type() === 'error') console.error(`Browser console error: ${message.text()}`)
  })
  page.on('response', (response) => {
    if (response.status() >= 400 && response.url().includes('/api/v1/')) {
      apiFailures.push(`${response.status()} ${response.request().method()} ${response.url()}`)
    }
  })

  try {
    await page.goto(`${baseUrl}/#/login`, { waitUntil: 'networkidle' })
    await page.getByLabel('一言SQL').waitFor({ timeout: 20_000 })
    await page.getByRole('heading', { name: '账号登录' }).waitFor({ timeout: 20_000 })
    await page.screenshot({
      path: path.join(root, 'docs', 'adaptive', 'brand-login-smoke.png'),
      fullPage: true,
    })

    const inputs = page.locator('input')
    await inputs.nth(0).fill(process.env.ADAPTIVE_UI_USERNAME || 'admin')
    await inputs.nth(1).fill(process.env.ADAPTIVE_UI_PASSWORD || 'SQLBot@123456')
    await page.locator('.login-btn').click()
    await page.waitForURL((url) => !url.hash.includes('/login'), { timeout: 30_000 })
    await page.getByLabel('一言SQL').first().waitFor({ timeout: 20_000 })
    await page.screenshot({
      path: path.join(root, 'docs', 'adaptive', 'brand-workspace-smoke.png'),
      fullPage: true,
    })

    await page.goto(`${baseUrl}/#/set/member`, { waitUntil: 'networkidle' })
    await page.waitForTimeout(1_000)
    if (apiFailures.length) {
      throw new Error(`Member management API failures detected:\n${apiFailures.join('\n')}`)
    }

    await page.evaluate(() => {
      window.location.hash = '#/system/setting/appearance'
    })
    await page.waitForURL((url) => url.hash.includes('/system/setting/appearance'))
    await page.locator('.right-main .appearance').waitFor({ timeout: 20_000 })
    const blueThemeButton = page.locator('.appearance .theme-color .ed-button').nth(0)
    if (!(await blueThemeButton.evaluate((element) => element.classList.contains('is-active')))) {
      throw new Error('Appearance settings did not select the blue theme by default')
    }
    await page.evaluate(() => {
      window.location.hash = '#/system/user'
    })
    await page.waitForURL((url) => url.hash.includes('/system/user'))
    await page.locator('.right-main .sqlbot-table-container').waitFor({ timeout: 20_000 })
    await page.evaluate(() => {
      window.location.hash = '#/system/audit'
    })
    await page.waitForURL((url) => url.hash.includes('/system/audit'))
    await page.locator('.right-main .professional').waitFor({ timeout: 20_000 })
    await page.locator('.right-main .ed-table__row').first().waitFor({ timeout: 20_000 })
    if (apiFailures.length) {
      throw new Error(`System audit API failures detected:\n${apiFailures.join('\n')}`)
    }
    await page.evaluate(() => {
      window.location.hash = '#/set/member'
    })
    await page.waitForURL((url) => url.hash.includes('/set/member'))

    await page.locator('.left-side .ed-sub-menu__title').filter({ hasText: '设置' }).click()
    await page.locator('.left-side .ed-menu-item').filter({ hasText: '术语配置' }).click()
    const activeParent = page.locator('.ed-sub-menu.is-active.is-opened > .ed-sub-menu__title')
    const activeChild = page.locator('.ed-sub-menu.is-opened .ed-menu-item.is-active')
    await activeParent.waitFor({ timeout: 20_000 })
    await activeChild.waitFor({ timeout: 20_000 })
    const parentBackground = await activeParent.evaluate(
      (element) => getComputedStyle(element).backgroundImage
    )
    const childBackground = await activeChild.evaluate(
      (element) => getComputedStyle(element).backgroundImage
    )
    if (parentBackground !== 'none' || childBackground === 'none') {
      throw new Error(
        `Nested menu selection is incorrect: parent=${parentBackground}, child=${childBackground}`
      )
    }
    await page.screenshot({
      path: path.join(root, 'docs', 'adaptive', 'brand-submenu-smoke.png'),
      fullPage: true,
    })

    await page.goto(`${baseUrl}/#/system/user`, { waitUntil: 'networkidle' })
    await page.locator('.table-operate .action-btn').nth(1).click()
    const passwordDialog = page.locator('.ed-dialog').filter({ visible: true }).last()
    await passwordDialog.locator('input').nth(0).waitFor({ timeout: 20_000 })
    await passwordDialog.locator('.dialog-footer .ed-button').first().click()
    await page.getByRole('button', { name: '添加用户' }).click()
    await page.getByText('数据源', { exact: true }).last().waitFor({ timeout: 20_000 })
    const workspaceField = page
      .locator('.ed-drawer .ed-form-item')
      .filter({ hasText: '工作空间' })
      .first()
    await workspaceField.locator('.ed-select').click()
    await page.locator('.ed-select-dropdown__item').filter({ visible: true }).first().click()
    await page.waitForTimeout(1_000)
    if (apiFailures.length) {
      throw new Error(`API failures detected:\n${apiFailures.join('\n')}`)
    }

    console.log('一言SQL brand smoke test passed')
  } finally {
    await browser.close()
  }
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
