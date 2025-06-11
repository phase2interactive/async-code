import { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class TasksPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate() {
    await super.navigate('/tasks');
  }

  async createNewTask(taskData: {
    title: string;
    description: string;
    projectId?: string;
    model?: string;
  }) {
    // Click create task button
    await this.clickButton('Create Task');
    
    // Fill task form
    await this.fillInput('Title', taskData.title);
    await this.fillInput('Description', taskData.description);
    
    // Select project if provided
    if (taskData.projectId) {
      await this.page.selectOption('select[name="projectId"]', taskData.projectId);
    }
    
    // Select model if provided
    if (taskData.model) {
      await this.page.selectOption('select[name="model"]', taskData.model);
    }
    
    // Submit form
    await this.clickButton('Create');
    
    // Wait for task to be created
    await this.page.waitForURL(/\/tasks\/[a-zA-Z0-9-]+/, { timeout: 30000 });
  }

  async getTaskStatus(taskId: string): Promise<string | null> {
    const statusElement = await this.page.locator(`[data-task-id="${taskId}"] .task-status`).first();
    if (await statusElement.isVisible()) {
      return await statusElement.textContent();
    }
    return null;
  }

  async waitForTaskCompletion(taskId: string, timeout: number = 300000) {
    await this.page.waitForFunction(
      async (id) => {
        const statusElement = document.querySelector(`[data-task-id="${id}"] .task-status`);
        return statusElement?.textContent?.toLowerCase() === 'completed';
      },
      taskId,
      { timeout }
    );
  }

  async viewTaskDetails(taskId: string) {
    await this.page.click(`[data-task-id="${taskId}"]`);
    await this.page.waitForURL(`/tasks/${taskId}`);
  }

  async getTaskList(): Promise<Array<{ id: string; title: string; status: string }>> {
    const tasks = await this.page.locator('.task-item').all();
    const taskList = [];
    
    for (const task of tasks) {
      const id = await task.getAttribute('data-task-id') || '';
      const title = await task.locator('.task-title').textContent() || '';
      const status = await task.locator('.task-status').textContent() || '';
      taskList.push({ id, title, status });
    }
    
    return taskList;
  }
}