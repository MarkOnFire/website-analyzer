#!/usr/bin/env node
/**
 * MCP Server for Website Analyzer.
 *
 * This server exposes tools for Claude to interact with the Website Analyzer
 * Python CLI, enabling crawling, testing, and issue tracking through MCP.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import { logger } from "./logger.js";
import { jobManager } from "./job-manager.js";
import {
  ListTestsInputSchema,
  ListProjectsInputSchema,
  StartAnalysisInputSchema,
  CheckStatusInputSchema,
  ViewIssuesInputSchema,
  RerunTestsInputSchema,
} from "./types.js";
import { executePythonCLI, spawnPythonCLI, parseProgress } from "./cli-executor.js";
import { readdir, readFile } from "fs/promises";
import { join } from "path";

// Create the MCP server
const server = new Server(
  {
    name: "website-analyzer",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define available tools
const TOOLS = [
  {
    name: "list_tests",
    description: "List all available test plugins for website analysis",
    inputSchema: {
      type: "object",
      properties: {},
      required: [],
    },
  },
  {
    name: "list_projects",
    description: "List all website analysis projects in the workspace",
    inputSchema: {
      type: "object",
      properties: {
        includeSnapshots: {
          type: "boolean",
          description: "Include snapshot count for each project",
          default: false,
        },
      },
      required: [],
    },
  },
  {
    name: "start_analysis",
    description: "Start a new website analysis job. Crawls the site and runs specified tests.",
    inputSchema: {
      type: "object",
      properties: {
        url: {
          type: "string",
          description: "The URL of the website to analyze",
        },
        tests: {
          type: "array",
          items: { type: "string" },
          description: "List of test names to run (omit for all tests)",
        },
        maxPages: {
          type: "number",
          description: "Maximum pages to crawl (default: 1000)",
          default: 1000,
        },
        maxDepth: {
          type: "number",
          description: "Maximum crawl depth (optional)",
        },
        recrawl: {
          type: "boolean",
          description: "Force recrawl even if recent snapshot exists",
          default: false,
        },
      },
      required: ["url"],
    },
  },
  {
    name: "check_status",
    description: "Check the status of a running or completed analysis job",
    inputSchema: {
      type: "object",
      properties: {
        jobId: {
          type: "string",
          description: "The job ID returned from start_analysis",
        },
      },
      required: ["jobId"],
    },
  },
  {
    name: "view_issues",
    description: "View issues found during website analysis",
    inputSchema: {
      type: "object",
      properties: {
        projectSlug: {
          type: "string",
          description: "The project slug (derived from URL)",
        },
        testName: {
          type: "string",
          description: "Filter by test name",
        },
        priority: {
          type: "string",
          enum: ["critical", "high", "medium", "low"],
          description: "Filter by priority level",
        },
        status: {
          type: "string",
          enum: ["open", "investigating", "fixed", "verified"],
          description: "Filter by issue status",
        },
        limit: {
          type: "number",
          description: "Maximum issues to return (default: 50)",
          default: 50,
        },
      },
      required: ["projectSlug"],
    },
  },
  {
    name: "rerun_tests",
    description: "Rerun tests on an existing project, optionally with a fresh crawl",
    inputSchema: {
      type: "object",
      properties: {
        projectSlug: {
          type: "string",
          description: "The project slug to rerun tests for",
        },
        tests: {
          type: "array",
          items: { type: "string" },
          description: "List of test names to run (omit for all tests)",
        },
        recrawl: {
          type: "boolean",
          description: "Perform a fresh crawl before running tests",
          default: false,
        },
      },
      required: ["projectSlug"],
    },
  },
] as const;

// Handle list_tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
  logger.debug("Listing tools");
  return { tools: TOOLS };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  logger.info({ tool: name, args }, "Tool called");

  try {
    switch (name) {
      case "list_tests": {
        ListTestsInputSchema.parse(args);

        // Return the known built-in test plugins
        const tests = [
          {
            name: "migration-scanner",
            description: "Scans for deprecated code patterns and migration issues",
          },
          {
            name: "seo-optimizer",
            description: "Analyzes SEO factors including meta tags, headings, and links",
          },
          {
            name: "llm-optimizer",
            description: "Checks content structure for LLM/AI discoverability",
          },
          {
            name: "security-audit",
            description: "Audits security headers, HTTPS usage, and vulnerabilities",
          },
        ];

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ tests }, null, 2),
            },
          ],
        };
      }

      case "list_projects": {
        const input = ListProjectsInputSchema.parse(args);

        try {
          const projectsDir = join("/Users/mriechers/Developer/website-analyzer", "projects");
          const entries = await readdir(projectsDir, { withFileTypes: true });
          const projects = [];

          for (const entry of entries) {
            if (!entry.isDirectory()) continue;

            try {
              const metadataPath = join(projectsDir, entry.name, "metadata.json");
              const metadataContent = await readFile(metadataPath, "utf-8");
              const metadata = JSON.parse(metadataContent);

              const projectInfo: any = {
                slug: entry.name,
                url: metadata.url || "unknown",
                createdAt: metadata.created_at || metadata.createdAt || "unknown",
                lastCrawl: metadata.last_crawl || metadata.lastCrawl,
              };

              if (input.includeSnapshots) {
                try {
                  const snapshotsDir = join(projectsDir, entry.name, "snapshots");
                  const snapshots = await readdir(snapshotsDir);
                  projectInfo.snapshotCount = snapshots.length;
                } catch {
                  projectInfo.snapshotCount = 0;
                }
              }

              projects.push(projectInfo);
            } catch (error) {
              logger.warn({ project: entry.name, error }, "Failed to read project metadata");
            }
          }

          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({ projects }, null, 2),
              },
            ],
          };
        } catch (error) {
          logger.error({ error }, "Failed to list projects");
          // Return empty list if projects directory doesn't exist
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  projects: [],
                  message: "No projects found. Use start_analysis to create one.",
                }, null, 2),
              },
            ],
          };
        }
      }

      case "start_analysis": {
        const input = StartAnalysisInputSchema.parse(args);

        // Create a slug from URL
        const projectSlug = input.url
          .replace(/https?:\/\//, "")
          .replace(/\/$/, "")
          .replace(/[^a-z0-9.-]/gi, "-")
          .toLowerCase();
        const job = jobManager.createJob("full_analysis", projectSlug);

        try {
          // First, create the project (ignore error if it already exists)
          logger.info({ url: input.url, slug: projectSlug }, "Creating project");
          const createResult = await executePythonCLI(["project", "new", input.url]);
          if (createResult.exitCode !== 0 && !createResult.stderr.includes("already exists")) {
            throw new Error(`Failed to create project: ${createResult.stderr}`);
          }

          // Build crawl CLI arguments
          const cliArgs = ["crawl", "start", projectSlug];

          if (input.maxPages) {
            cliArgs.push("--max-pages", input.maxPages.toString());
          }

          if (input.maxDepth) {
            cliArgs.push("--max-depth", input.maxDepth.toString());
          }

          // Spawn Python CLI process
          const process = spawnPythonCLI(cliArgs);
          jobManager.attachProcess(job.id, process);

          // Set 30-minute timeout for analysis jobs
          jobManager.setTimeout(job.id, 30 * 60 * 1000);

          // Update job status to running
          jobManager.updateJobStatus(job.id, "running");

          // Setup stdout/stderr handlers for progress tracking
          let stdoutBuffer = "";
          let stderrBuffer = "";

          process.stdout?.on("data", (data) => {
            const text = data.toString();
            stdoutBuffer += text;

            // Parse progress from each line
            const lines = stdoutBuffer.split("\n");
            stdoutBuffer = lines.pop() || ""; // Keep incomplete line in buffer

            for (const line of lines) {
              const progress = parseProgress(line);
              if (progress) {
                jobManager.updateProgress(job.id, progress.current, progress.total, progress.message);
              }
              logger.debug({ jobId: job.id, line }, "CLI stdout");
            }
          });

          process.stderr?.on("data", (data) => {
            stderrBuffer += data.toString();
            logger.warn({ jobId: job.id, stderr: data.toString() }, "CLI stderr");
          });

          process.on("error", (error) => {
            logger.error({ jobId: job.id, error }, "Process spawn error");
            jobManager.updateJobStatus(job.id, "failed", {
              error: `Process spawn failed: ${error.message}`,
              completedAt: new Date().toISOString(),
            });
            jobManager.clearTimeout(job.id);
            jobManager.detachProcess(job.id);
          });

          process.on("close", (exitCode, signal) => {
            logger.info({ jobId: job.id, exitCode, signal }, "Process completed");
            jobManager.clearTimeout(job.id);
            jobManager.detachProcess(job.id);

            if (exitCode === 0) {
              jobManager.updateJobStatus(job.id, "completed", {
                result: { projectSlug, message: "Analysis completed successfully" },
                completedAt: new Date().toISOString(),
              });
            } else {
              jobManager.updateJobStatus(job.id, "failed", {
                error: `Process exited with code ${exitCode}: ${stderrBuffer}`,
                completedAt: new Date().toISOString(),
              });
            }
          });

          logger.info({ jobId: job.id, url: input.url }, "Started analysis job");

          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  jobId: job.id,
                  message: `Analysis job started for ${input.url}. Use check_status to monitor progress.`,
                  projectSlug,
                }, null, 2),
              },
            ],
          };
        } catch (error) {
          logger.error({ jobId: job.id, error }, "Failed to start analysis");
          jobManager.updateJobStatus(job.id, "failed", {
            error: error instanceof Error ? error.message : String(error),
            completedAt: new Date().toISOString(),
          });
          throw error;
        }
      }

      case "check_status": {
        const input = CheckStatusInputSchema.parse(args);
        const job = jobManager.getJob(input.jobId);

        if (!job) {
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({ error: `Job ${input.jobId} not found` }),
              },
            ],
            isError: true,
          };
        }

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                jobId: job.id,
                status: job.status,
                progress: job.progress,
                result: job.result,
                error: job.error,
              }, null, 2),
            },
          ],
        };
      }

      case "view_issues": {
        const input = ViewIssuesInputSchema.parse(args);

        try {
          const issuesPath = join(
            "/Users/mriechers/Developer/website-analyzer",
            "projects",
            input.projectSlug,
            "issues.json"
          );

          const issuesContent = await readFile(issuesPath, "utf-8");
          const issuesData = JSON.parse(issuesContent);
          let issues = issuesData.issues || [];

          // Apply filters
          if (input.testName) {
            issues = issues.filter((issue: any) => issue.test_name === input.testName || issue.testName === input.testName);
          }

          if (input.priority) {
            issues = issues.filter((issue: any) => issue.priority === input.priority);
          }

          if (input.status) {
            issues = issues.filter((issue: any) => issue.status === input.status);
          }

          // Apply limit
          const totalCount = issues.length;
          issues = issues.slice(0, input.limit || 50);

          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  issues,
                  totalCount,
                  returned: issues.length,
                }, null, 2),
              },
            ],
          };
        } catch (error) {
          logger.warn({ projectSlug: input.projectSlug, error }, "Failed to read issues");
          // Return empty if issues.json doesn't exist
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  issues: [],
                  totalCount: 0,
                  message: `No issues found for project: ${input.projectSlug}`,
                }, null, 2),
              },
            ],
          };
        }
      }

      case "rerun_tests": {
        const input = RerunTestsInputSchema.parse(args);
        const job = jobManager.createJob("test", input.projectSlug);

        try {
          // Build CLI arguments
          const cliArgs = ["test", "run", input.projectSlug];

          if (input.tests && input.tests.length > 0) {
            cliArgs.push("--tests", input.tests.join(","));
          }

          if (input.recrawl) {
            cliArgs.push("--recrawl");
          }

          // Spawn Python CLI process
          const process = spawnPythonCLI(cliArgs);
          jobManager.attachProcess(job.id, process);

          // Set 20-minute timeout for test jobs
          jobManager.setTimeout(job.id, 20 * 60 * 1000);

          // Update job status to running
          jobManager.updateJobStatus(job.id, "running");

          // Setup stdout/stderr handlers
          let stdoutBuffer = "";
          let stderrBuffer = "";

          process.stdout?.on("data", (data) => {
            const text = data.toString();
            stdoutBuffer += text;

            const lines = stdoutBuffer.split("\n");
            stdoutBuffer = lines.pop() || "";

            for (const line of lines) {
              const progress = parseProgress(line);
              if (progress) {
                jobManager.updateProgress(job.id, progress.current, progress.total, progress.message);
              }
              logger.debug({ jobId: job.id, line }, "CLI stdout");
            }
          });

          process.stderr?.on("data", (data) => {
            stderrBuffer += data.toString();
            logger.warn({ jobId: job.id, stderr: data.toString() }, "CLI stderr");
          });

          process.on("error", (error) => {
            logger.error({ jobId: job.id, error }, "Process spawn error");
            jobManager.updateJobStatus(job.id, "failed", {
              error: `Process spawn failed: ${error.message}`,
              completedAt: new Date().toISOString(),
            });
            jobManager.clearTimeout(job.id);
            jobManager.detachProcess(job.id);
          });

          process.on("close", (exitCode, signal) => {
            logger.info({ jobId: job.id, exitCode, signal }, "Process completed");
            jobManager.clearTimeout(job.id);
            jobManager.detachProcess(job.id);

            if (exitCode === 0) {
              jobManager.updateJobStatus(job.id, "completed", {
                result: { projectSlug: input.projectSlug, message: "Tests completed successfully" },
                completedAt: new Date().toISOString(),
              });
            } else {
              jobManager.updateJobStatus(job.id, "failed", {
                error: `Process exited with code ${exitCode}: ${stderrBuffer}`,
                completedAt: new Date().toISOString(),
              });
            }
          });

          logger.info({ jobId: job.id, projectSlug: input.projectSlug }, "Started test rerun job");

          return {
            content: [
              {
                type: "text",
                text: JSON.stringify({
                  jobId: job.id,
                  message: `Test rerun job started for ${input.projectSlug}. Use check_status to monitor.`,
                }, null, 2),
              },
            ],
          };
        } catch (error) {
          logger.error({ jobId: job.id, error }, "Failed to start test rerun");
          jobManager.updateJobStatus(job.id, "failed", {
            error: error instanceof Error ? error.message : String(error),
            completedAt: new Date().toISOString(),
          });
          throw error;
        }
      }

      default:
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: `Unknown tool: ${name}` }),
            },
          ],
          isError: true,
        };
    }
  } catch (error) {
    logger.error({ error, tool: name }, "Tool execution failed");
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: error instanceof Error ? error.message : String(error),
          }),
        },
      ],
      isError: true,
    };
  }
});

// Start the server
async function main() {
  logger.info("Starting Website Analyzer MCP server");

  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info("MCP server connected and ready");
}

main().catch((error) => {
  logger.fatal({ error }, "Failed to start server");
  process.exit(1);
});
