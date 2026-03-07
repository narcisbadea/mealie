import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Menu Reorganization (Task #3)
 * Tests verify sidebar structure, tab interfaces, and navigation
 *
 * > **Shield** `sonnet` · 2026-03-05T10:30:00Z
 */

test.describe('Main Sidebar Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin user
    await page.goto('/login');
    await page.getByLabel('Email or Username', { exact: true }).fill('changeme@example.com');
    await page.getByLabel('Password', { exact: true }).fill('MyPassword');
    await page.getByRole('button', { name: 'Login', exact: true }).click();
    // Skip admin setup page if it appears
    const skipLink = page.getByRole('link', { name: "I'm already set up, just bring me to the homepage" });
    if (await skipLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await skipLink.click();
    }
    await expect(page).toHaveURL(/\/g\//);
  });

  test('main sidebar shows primary navigation items', async ({ page }) => {
    // Open sidebar if not visible
    const menuButton = page.getByRole('button', { name: /menu/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();
    }

    // Verify primary navigation items are visible
    await expect(page.getByRole('link', { name: /recipes/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /meal plan/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /shopping list/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /cookbooks/i })).toBeVisible();
  });

  test('organize dropdown contains correct items', async ({ page }) => {
    // Open sidebar if not visible
    const menuButton = page.getByRole('button', { name: /menu/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();
    }

    // Click on Organize dropdown
    const organizeButton = page.getByRole('button', { name: /organize/i });
    await organizeButton.click();

    // Verify Organize dropdown items
    await expect(page.getByRole('link', { name: /timeline/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /categories/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /tags/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /tools/i })).toBeVisible();
  });

  test('shopping lists link navigates correctly', async ({ page }) => {
    // Open sidebar if not visible
    const menuButton = page.getByRole('button', { name: /menu/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();
    }

    await page.getByRole('link', { name: /shopping list/i }).first().click();
    await expect(page).toHaveURL(/\/shopping-lists/);
  });

  test('cookbooks link navigates correctly', async ({ page }) => {
    // Open sidebar if not visible
    const menuButton = page.getByRole('button', { name: /menu/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();
    }

    await page.getByRole('link', { name: /cookbooks/i }).first().click();
    await expect(page).toHaveURL(/\/cookbooks/);
  });
});

test.describe('Admin Sidebar Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin user
    await page.goto('/login');
    await page.getByLabel('Email or Username', { exact: true }).fill('changeme@example.com');
    await page.getByLabel('Password', { exact: true }).fill('MyPassword');
    await page.getByRole('button', { name: 'Login', exact: true }).click();
    // Skip admin setup page if it appears
    const skipLink = page.getByRole('link', { name: "I'm already set up, just bring me to the homepage" });
    if (await skipLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await skipLink.click();
    }
  });

  test('admin sidebar shows Users & Access dropdown', async ({ page }) => {
    // Navigate to admin area
    await page.goto('/admin/site-settings');

    // Verify Users & Access dropdown exists
    const usersAccessButton = page.getByRole('button', { name: /users.*access/i });
    await expect(usersAccessButton).toBeVisible();

    // Expand dropdown and verify items
    await usersAccessButton.click();
    await expect(page.getByRole('link', { name: /users/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /households/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /groups/i })).toBeVisible();
  });

  test('admin sidebar shows System dropdown', async ({ page }) => {
    // Navigate to admin area
    await page.goto('/admin/site-settings');

    // Verify System dropdown exists
    const systemButton = page.getByRole('button', { name: /system/i });
    await expect(systemButton).toBeVisible();

    // Expand dropdown and verify items
    await systemButton.click();
    await expect(page.getByRole('link', { name: /backups/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /maintenance/i })).toBeVisible();
  });

  test('admin sidebar shows Developer section', async ({ page }) => {
    // Navigate to admin area
    await page.goto('/admin/site-settings');

    // Verify Developer section exists
    const developerButton = page.getByRole('button', { name: /debug/i });
    await expect(developerButton).toBeVisible();

    // Expand dropdown and verify items
    await developerButton.click();
    await expect(page.getByRole('link', { name: /openai/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /parser/i })).toBeVisible();
  });

  test('admin site settings link works', async ({ page }) => {
    await page.goto('/admin/site-settings');
    await expect(page).toHaveURL(/\/admin\/site-settings/);
  });
});

test.describe('User Profile Tabbed Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Login as regular user
    await page.goto('/login');
    await page.getByLabel('Email or Username', { exact: true }).fill('changeme@example.com');
    await page.getByLabel('Password', { exact: true }).fill('MyPassword');
    await page.getByRole('button', { name: 'Login', exact: true }).click();
    // Skip admin setup page if it appears
    const skipLink = page.getByRole('link', { name: "I'm already set up, just bring me to the homepage" });
    if (await skipLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await skipLink.click();
    }
  });

  test('user profile page shows tabbed interface', async ({ page }) => {
    await page.goto('/user/profile');

    // Verify all tabs are present
    await expect(page.getByRole('tab', { name: /profile/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /preferences/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /api.*token/i })).toBeVisible();
  });

  test('profile tab is active by default', async ({ page }) => {
    await page.goto('/user/profile');

    // Profile tab should be active
    const profileTab = page.getByRole('tab', { name: /profile/i });
    await expect(profileTab).toHaveAttribute('aria-selected', 'true');
  });

  test('switching to preferences tab shows preferences content', async ({ page }) => {
    await page.goto('/user/profile');

    // Click preferences tab
    await page.getByRole('tab', { name: /preferences/i }).click();

    // Verify preferences content is visible
    await expect(page.getByText(/default activity/i)).toBeVisible();
    await expect(page.getByText(/advanced/i)).toBeVisible();
  });

  test('switching to API tokens tab shows tokens content', async ({ page }) => {
    await page.goto('/user/profile');

    // Click API tokens tab
    await page.getByRole('tab', { name: /api.*token/i }).click();

    // Verify API tokens content is visible
    await expect(page.getByRole('button', { name: /create/i })).toBeVisible();
  });

  test('existing route /user/profile/edit redirects to profile page', async ({ page }) => {
    await page.goto('/user/profile/edit');

    // Should be on profile page with profile tab active
    await expect(page).toHaveURL(/\/user\/profile/);
    await expect(page.getByRole('tab', { name: /profile/i })).toBeVisible();
  });

  test('existing route /user/profile/api-tokens redirects to profile page', async ({ page }) => {
    await page.goto('/user/profile/api-tokens');

    // Should be on profile page
    await expect(page).toHaveURL(/\/user\/profile/);
    await expect(page.getByRole('tab', { name: /api.*token/i })).toBeVisible();
  });
});

test.describe('Household Settings Tabbed Interface', () => {
  test.beforeEach(async ({ page }) => {
    // Login as user who can manage household
    await page.goto('/login');
    await page.getByLabel('Email or Username', { exact: true }).fill('changeme@example.com');
    await page.getByLabel('Password', { exact: true }).fill('MyPassword');
    await page.getByRole('button', { name: 'Login', exact: true }).click();
    // Skip admin setup page if it appears
    const skipLink = page.getByRole('link', { name: "I'm already set up, just bring me to the homepage" });
    if (await skipLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await skipLink.click();
    }
  });

  test('household settings page shows tabbed interface', async ({ page }) => {
    await page.goto('/household');

    // Verify all tabs are present
    await expect(page.getByRole('tab', { name: /general/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /members/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /notification/i })).toBeVisible();
  });

  test('general tab is active by default', async ({ page }) => {
    await page.goto('/household');

    // General tab should be active
    const generalTab = page.getByRole('tab', { name: /general/i });
    await expect(generalTab).toHaveAttribute('aria-selected', 'true');
  });

  test('switching to members tab shows members content', async ({ page }) => {
    await page.goto('/household');

    // Click members tab
    await page.getByRole('tab', { name: /members/i }).click();

    // Verify members table is visible
    await expect(page.getByRole('table')).toBeVisible();
    await expect(page.getByText(/username/i)).toBeVisible();
  });

  test('switching to notifications tab shows notifications content', async ({ page }) => {
    await page.goto('/household');

    // Click notifications tab
    await page.getByRole('tab', { name: /notification/i }).click();

    // Verify notifications content is visible (create button)
    await expect(page.getByRole('button', { name: /create/i })).toBeVisible();
  });

  test('existing route /household/members redirects to household page', async ({ page }) => {
    await page.goto('/household/members');

    // Should be on household page
    await expect(page).toHaveURL(/\/household/);
  });
});

test.describe('Settings Menu Access', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin user
    await page.goto('/login');
    await page.getByLabel('Email or Username', { exact: true }).fill('changeme@example.com');
    await page.getByLabel('Password', { exact: true }).fill('MyPassword');
    await page.getByRole('button', { name: 'Login', exact: true }).click();
    // Skip admin setup page if it appears
    const skipLink = page.getByRole('link', { name: "I'm already set up, just bring me to the homepage" });
    if (await skipLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await skipLink.click();
    }
  });

  test('settings menu shows user settings option', async ({ page }) => {
    // Click settings button
    await page.getByRole('button', { name: /settings/i }).click();

    // Verify user settings option is visible
    await expect(page.getByRole('listitem').filter({ hasText: /user settings/i })).toBeVisible();
  });

  test('settings menu shows admin settings for admin users', async ({ page }) => {
    // Click settings button
    await page.getByRole('button', { name: /settings/i }).click();

    // Verify admin settings option is visible
    await expect(page.getByRole('listitem').filter({ hasText: /admin settings/i })).toBeVisible();
  });

  test('settings menu navigates to user profile', async ({ page }) => {
    // Click settings button
    await page.getByRole('button', { name: /settings/i }).click();

    // Click user settings
    await page.getByRole('listitem').filter({ hasText: /user settings/i }).click();

    await expect(page).toHaveURL(/\/user\/profile/);
  });

  test('settings menu navigates to admin settings', async ({ page }) => {
    // Click settings button
    await page.getByRole('button', { name: /settings/i }).click();

    // Click admin settings
    await page.getByRole('listitem').filter({ hasText: /admin settings/i }).click();

    await expect(page).toHaveURL(/\/admin\/site-settings/);
  });
});