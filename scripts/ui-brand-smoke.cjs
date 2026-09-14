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
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } })

  try {
    await page.goto(`${baseUrl}/#/login`, { waitUntil: 'networkidle' })
    await page.getByLabel('一言SQL').waitFor({ timeout: 20_000 })
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

    console.log('一言SQL brand smoke test passed')
  } finally {
    await browser.close()
  }
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
