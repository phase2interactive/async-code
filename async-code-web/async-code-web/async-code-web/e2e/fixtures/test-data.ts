import { createClient } from '@supabase/supabase-js';
import { testConfig } from '../config/test.config';

const supabase = createClient(
  testConfig.supabase.url,
  testConfig.supabase.anonKey
);

export interface TestUser {
  id: string;
  email: string;
  password: string;
}

export interface TestProject {
  id: string;
  name: string;
  description: string;
  repo_url: string;
  user_id: string;
}

export interface TestTask {
  id: string;
  title: string;
  description: string;
  project_id: string;
  user_id: string;
  status: string;
  model: string;
}

export class TestDataSeeder {
  static async createTestUser(): Promise<TestUser> {
    const { data, error } = await supabase.auth.signUp({
      email: testConfig.testUser.email,
      password: testConfig.testUser.password,
    });

    if (error) {
      console.error('Error creating test user:', error);
      throw error;
    }

    return {
      id: data.user?.id || '',
      email: testConfig.testUser.email,
      password: testConfig.testUser.password,
    };
  }

  static async ensureTestUser(): Promise<TestUser> {
    // Try to sign in first
    const { data, error } = await supabase.auth.signInWithPassword({
      email: testConfig.testUser.email,
      password: testConfig.testUser.password,
    });

    if (!error && data.user) {
      return {
        id: data.user.id,
        email: testConfig.testUser.email,
        password: testConfig.testUser.password,
      };
    }

    // If sign in fails, create new user
    return await this.createTestUser();
  }

  static async createTestProject(userId: string): Promise<TestProject> {
    const project = {
      name: `Test Project ${Date.now()}`,
      description: 'E2E test project',
      repo_url: testConfig.github.testRepo,
      repo_name: testConfig.github.testRepo.split('/')[1],
      repo_owner: testConfig.github.testRepo.split('/')[0],
      user_id: userId,
      settings: {
        github_token: testConfig.github.token,
      },
    };

    const { data, error } = await supabase
      .from('projects')
      .insert([project])
      .select()
      .single();

    if (error) {
      console.error('Error creating test project:', error);
      throw error;
    }

    return data;
  }

  static async cleanupTestData(userId: string) {
    // Delete test tasks
    await supabase
      .from('tasks')
      .delete()
      .eq('user_id', userId);

    // Delete test projects
    await supabase
      .from('projects')
      .delete()
      .eq('user_id', userId);
  }

  static async setupTestEnvironment(): Promise<{
    user: TestUser;
    project: TestProject;
  }> {
    const user = await this.ensureTestUser();
    await this.cleanupTestData(user.id);
    const project = await this.createTestProject(user.id);

    return { user, project };
  }

  static async teardownTestEnvironment(userId: string) {
    await this.cleanupTestData(userId);
    await supabase.auth.signOut();
  }
}