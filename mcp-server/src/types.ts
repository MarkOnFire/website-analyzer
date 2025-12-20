/**
 * TypeScript types for MCP tool inputs and outputs.
 */

import { z } from "zod";

// Job management types
export interface Job {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  type: "crawl" | "test" | "full_analysis";
  projectSlug: string;
  startedAt: string;
  completedAt?: string;
  progress?: {
    current: number;
    total: number;
    message: string;
  };
  result?: unknown;
  error?: string;
}

// Tool input schemas (using Zod for validation)
export const ListTestsInputSchema = z.object({});
export type ListTestsInput = z.infer<typeof ListTestsInputSchema>;

export interface ListTestsOutput {
  tests: Array<{
    name: string;
    description: string;
    category: string;
  }>;
}

export const ListProjectsInputSchema = z.object({
  includeSnapshots: z.boolean().optional().default(false),
});
export type ListProjectsInput = z.infer<typeof ListProjectsInputSchema>;

export interface ListProjectsOutput {
  projects: Array<{
    slug: string;
    url: string;
    createdAt: string;
    lastCrawl?: string;
    snapshotCount?: number;
  }>;
}

export const StartAnalysisInputSchema = z.object({
  url: z.string().url(),
  tests: z.array(z.string()).optional(),
  maxPages: z.number().positive().optional().default(1000),
  maxDepth: z.number().positive().optional(),
  recrawl: z.boolean().optional().default(false),
});
export type StartAnalysisInput = z.infer<typeof StartAnalysisInputSchema>;

export interface StartAnalysisOutput {
  jobId: string;
  message: string;
  projectSlug: string;
}

export const CheckStatusInputSchema = z.object({
  jobId: z.string(),
});
export type CheckStatusInput = z.infer<typeof CheckStatusInputSchema>;

export interface CheckStatusOutput {
  jobId: string;
  status: Job["status"];
  progress?: Job["progress"];
  result?: unknown;
  error?: string;
}

export const ViewIssuesInputSchema = z.object({
  projectSlug: z.string(),
  testName: z.string().optional(),
  priority: z.enum(["critical", "high", "medium", "low"]).optional(),
  status: z.enum(["open", "investigating", "fixed", "verified"]).optional(),
  limit: z.number().positive().optional().default(50),
});
export type ViewIssuesInput = z.infer<typeof ViewIssuesInputSchema>;

export interface ViewIssuesOutput {
  issues: Array<{
    id: string;
    testName: string;
    priority: string;
    status: string;
    title: string;
    affectedUrls: string[];
    createdAt: string;
  }>;
  totalCount: number;
}

export const RerunTestsInputSchema = z.object({
  projectSlug: z.string(),
  tests: z.array(z.string()).optional(),
  recrawl: z.boolean().optional().default(false),
});
export type RerunTestsInput = z.infer<typeof RerunTestsInputSchema>;

export interface RerunTestsOutput {
  jobId: string;
  message: string;
}
