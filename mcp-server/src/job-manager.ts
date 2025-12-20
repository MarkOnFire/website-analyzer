/**
 * Job management for async analysis operations.
 */

import { ChildProcess } from "child_process";
import type { Job } from "./types.js";

/**
 * Generates a unique job ID.
 * Format: JOB-{timestamp}-{random}
 */
export function generateJobId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  return `JOB-${timestamp}-${random}`;
}

/**
 * In-memory job store for tracking running and completed jobs.
 */
export class JobManager {
  private jobs: Map<string, Job> = new Map();
  private processes: Map<string, ChildProcess> = new Map();
  private timeouts: Map<string, NodeJS.Timeout> = new Map();

  /**
   * Create a new job and return its ID.
   */
  createJob(
    type: Job["type"],
    projectSlug: string
  ): Job {
    const job: Job = {
      id: generateJobId(),
      status: "pending",
      type,
      projectSlug,
      startedAt: new Date().toISOString(),
    };
    this.jobs.set(job.id, job);
    return job;
  }

  /**
   * Get a job by ID.
   */
  getJob(jobId: string): Job | undefined {
    return this.jobs.get(jobId);
  }

  /**
   * Update job status.
   */
  updateJobStatus(
    jobId: string,
    status: Job["status"],
    updates?: Partial<Pick<Job, "progress" | "result" | "error" | "completedAt">>
  ): Job | undefined {
    const job = this.jobs.get(jobId);
    if (!job) return undefined;

    job.status = status;
    if (updates) {
      if (updates.progress !== undefined) job.progress = updates.progress;
      if (updates.result !== undefined) job.result = updates.result;
      if (updates.error !== undefined) job.error = updates.error;
      if (updates.completedAt !== undefined) job.completedAt = updates.completedAt;
    }

    if (status === "completed" || status === "failed") {
      job.completedAt = job.completedAt || new Date().toISOString();
    }

    return job;
  }

  /**
   * Update job progress.
   */
  updateProgress(
    jobId: string,
    current: number,
    total: number,
    message: string
  ): Job | undefined {
    const job = this.jobs.get(jobId);
    if (!job) return undefined;

    job.progress = { current, total, message };
    return job;
  }

  /**
   * List all jobs, optionally filtered by status.
   */
  listJobs(status?: Job["status"]): Job[] {
    const jobs = Array.from(this.jobs.values());
    if (status) {
      return jobs.filter((j) => j.status === status);
    }
    return jobs;
  }

  /**
   * Clean up old completed/failed jobs (older than 1 hour).
   */
  cleanup(): number {
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    let removed = 0;

    for (const [id, job] of this.jobs) {
      if (
        (job.status === "completed" || job.status === "failed") &&
        job.completedAt &&
        job.completedAt < oneHourAgo
      ) {
        this.jobs.delete(id);
        this.processes.delete(id);
        this.clearTimeout(id);
        removed++;
      }
    }

    return removed;
  }

  /**
   * Attach a child process to a job.
   */
  attachProcess(jobId: string, process: ChildProcess): void {
    this.processes.set(jobId, process);
  }

  /**
   * Get the process for a job.
   */
  getProcess(jobId: string): ChildProcess | undefined {
    return this.processes.get(jobId);
  }

  /**
   * Remove process tracking for a job.
   */
  detachProcess(jobId: string): void {
    this.processes.delete(jobId);
  }

  /**
   * Set a timeout for a job. If timeout is reached, kills the process and marks job as failed.
   */
  setTimeout(jobId: string, timeoutMs: number): void {
    const timeout = setTimeout(() => {
      const process = this.processes.get(jobId);
      if (process && !process.killed) {
        process.kill("SIGTERM");
      }
      this.updateJobStatus(jobId, "failed", {
        error: `Job timed out after ${timeoutMs}ms`,
        completedAt: new Date().toISOString(),
      });
      this.detachProcess(jobId);
    }, timeoutMs);

    this.timeouts.set(jobId, timeout);
  }

  /**
   * Clear timeout for a job.
   */
  clearTimeout(jobId: string): void {
    const timeout = this.timeouts.get(jobId);
    if (timeout) {
      clearTimeout(timeout);
      this.timeouts.delete(jobId);
    }
  }

  /**
   * Kill a running job and its process.
   */
  killJob(jobId: string): boolean {
    const process = this.processes.get(jobId);
    if (!process || process.killed) {
      return false;
    }

    process.kill("SIGTERM");
    this.clearTimeout(jobId);
    this.updateJobStatus(jobId, "failed", {
      error: "Job was manually killed",
      completedAt: new Date().toISOString(),
    });

    return true;
  }
}

// Singleton instance
export const jobManager = new JobManager();
