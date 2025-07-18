import { test, expect } from '@playwright/test'

test.describe('Content Analysis Flow', () => {
  test('should allow user to analyze content and view results', async ({ page }) => {
    await page.goto('http://localhost:5173/')

    // Navigate to Analyze page
    await page.click('text=Analyze Content')
    await expect(page).toHaveURL('http://localhost:5173/analyze')

    // Enter content
    const contentInput = page.locator('#content')
    await contentInput.fill('This is a sample content for testing purposes. It should be long enough for analysis.')

    // Click analyze button
    await page.click('text=Analyze Content')

    // Expect to navigate to results page
    await expect(page).toHaveURL(/http:\/\/localhost:5173\/results\/.+/)

    // Expect to see overall score
    await expect(page.locator('text=Overall Score')).toBeVisible()
    await expect(page.locator('text=/\d\.\d\/5/')).toBeVisible()

    // Expect to see category scores
    await expect(page.locator('text=Category Scores')).toBeVisible()

    // Expect to see detailed analysis
    await expect(page.locator('text=Detailed Analysis')).toBeVisible()
  })

  test('should allow user to select sample content and analyze', async ({ page }) => {
    await page.goto('http://localhost:5173/')

    // Navigate to Analyze page
    await page.click('text=Analyze Content')
    await expect(page).toHaveURL('http://localhost:5173/analyze')

    // Select sample content tab
    await page.click('text=Sample Content')

    // Select a sample
    await page.click('text=Marketing Blog Post Draft')

    // Expect content to be loaded into textarea
    const contentInput = page.locator('#content')
    await expect(contentInput).not.toBeEmpty()

    // Click analyze button
    await page.click('text=Analyze Content')

    // Expect to navigate to results page
    await expect(page).toHaveURL(/http:\/\/localhost:5173\/results\/.+/)

    // Expect to see overall score
    await expect(page.locator('text=Overall Score')).toBeVisible()
  })
})
