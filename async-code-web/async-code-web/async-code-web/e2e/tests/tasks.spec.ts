import { test, expect } from '../fixtures/test-helpers';
import { testConfig } from '../config/test.config';

test.describe('Task Creation and Execution', () => {
  test.beforeEach(async ({ authenticatedPage, settingsPage }) => {
    // Ensure GitHub token is set
    await settingsPage.navigate();
    await settingsPage.setGitHubToken(testConfig.github.token);
  });

  test('should create a new task', async ({ page, tasksPage, testData }) => {
    // Navigate to tasks page
    await tasksPage.navigate();
    
    // Create new task
    await tasksPage.createNewTask({
      title: 'Test Task - Fix Bug',
      description: 'Fix a simple bug in the code',
      projectId: testData.project.id,
      model: 'claude',
    });
    
    // Should redirect to task detail page
    await expect(page).toHaveURL(/\/tasks\/[a-zA-Z0-9-]+/);
    
    // Should show task title
    await expect(page.locator('h1')).toContainText('Test Task - Fix Bug');
    
    // Should show task status
    await expect(page.locator('.task-status')).toBeVisible();
  });

  test('should show task progress in real-time', async ({ page, tasksPage, testData }) => {
    // Create a task
    await tasksPage.navigate();
    await tasksPage.createNewTask({
      title: 'Test Task - Progress Check',
      description: 'Simple task to check progress updates',
      projectId: testData.project.id,
      model: 'claude',
    });
    
    // Get task ID from URL
    const url = page.url();
    const taskId = url.split('/').pop() || '';
    
    // Should show initial status
    const initialStatus = await page.locator('.task-status').textContent();
    expect(['pending', 'running']).toContain(initialStatus?.toLowerCase());
    
    // Wait for status to change (with timeout)
    await page.waitForFunction(
      () => {
        const status = document.querySelector('.task-status')?.textContent?.toLowerCase();
        return status === 'running' || status === 'completed' || status === 'failed';
      },
      { timeout: 30000 }
    );
    
    // Verify status changed
    const updatedStatus = await page.locator('.task-status').textContent();
    expect(updatedStatus?.toLowerCase()).not.toBe('pending');
  });

  test('should display task results when completed', async ({ page, tasksPage, testData }) => {
    // Create a simple task
    await tasksPage.navigate();
    await tasksPage.createNewTask({
      title: 'Test Task - Show Results',
      description: 'Add a comment to a function',
      projectId: testData.project.id,
      model: 'claude',
    });
    
    // Wait for task to complete (with shorter timeout for simple task)
    await page.waitForFunction(
      () => {
        const status = document.querySelector('.task-status')?.textContent?.toLowerCase();
        return status === 'completed' || status === 'failed';
      },
      { timeout: 120000 } // 2 minutes for simple task
    );
    
    const finalStatus = await page.locator('.task-status').textContent();
    
    if (finalStatus?.toLowerCase() === 'completed') {
      // Should show results section
      await expect(page.locator('[data-testid="task-results"]')).toBeVisible();
      
      // Should show diff viewer if changes were made
      const diffViewer = page.locator('[data-testid="diff-viewer"]');
      if (await diffViewer.isVisible()) {
        await expect(diffViewer).toContainText(/[\+\-]/); // Should contain diff markers
      }
    }
  });

  test('should list all tasks', async ({ page, tasksPage, testData }) => {
    // Create multiple tasks
    const taskTitles = ['Task 1', 'Task 2', 'Task 3'];
    
    for (const title of taskTitles) {
      await tasksPage.navigate();
      await tasksPage.createNewTask({
        title,
        description: `Description for ${title}`,
        projectId: testData.project.id,
        model: 'claude',
      });
      
      // Go back to tasks list
      await tasksPage.navigate();
    }
    
    // Get task list
    const tasks = await tasksPage.getTaskList();
    
    // Should have at least the tasks we created
    expect(tasks.length).toBeGreaterThanOrEqual(taskTitles.length);
    
    // Should contain our task titles
    const foundTitles = tasks.map(t => t.title);
    for (const title of taskTitles) {
      expect(foundTitles.some(t => t.includes(title))).toBeTruthy();
    }
  });

  test('should handle task creation errors gracefully', async ({ page, tasksPage, testData }) => {
    // Navigate to tasks page
    await tasksPage.navigate();
    
    // Try to create task without required fields
    await tasksPage.clickButton('Create Task');
    
    // Try to submit empty form
    await tasksPage.clickButton('Create');
    
    // Should show validation errors
    await expect(page.locator('text=required')).toBeVisible();
    
    // Should not navigate away
    await expect(page).toHaveURL('/tasks');
  });
});