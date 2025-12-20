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
        // TODO: Call Python CLI to get actual test list
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                tests: [
                  { name: "migration-scanner", description: "Scan for migration patterns", category: "migration" },
                  { name: "llm-optimizer", description: "Analyze LLM discoverability", category: "optimization" },
                  { name: "seo-optimizer", description: "SEO best practices check", category: "optimization" },
                  { name: "security-audit", description: "Security vulnerability scan", category: "security" },
                ],
              }, null, 2),
            },
          ],
        };
      }

      case "list_projects": {
        const input = ListProjectsInputSchema.parse(args);
        // TODO: Call Python CLI to get actual projects
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

      case "start_analysis": {
        const input = StartAnalysisInputSchema.parse(args);

        // Create a job
        const job = jobManager.createJob("full_analysis", input.url.replace(/https?:\/\//, "").replace(/[^a-z0-9]/gi, "-"));

        // TODO: Spawn Python CLI process for actual analysis
        logger.info({ jobId: job.id, url: input.url }, "Starting analysis job");

        // For now, just return the job info
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                jobId: job.id,
                message: `Analysis job created for ${input.url}. Use check_status to monitor progress.`,
                projectSlug: job.projectSlug,
              }, null, 2),
            },
          ],
        };
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
        // TODO: Read issues from project's issues.json
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

      case "rerun_tests": {
        const input = RerunTestsInputSchema.parse(args);
        const job = jobManager.createJob("test", input.projectSlug);

        logger.info({ jobId: job.id, projectSlug: input.projectSlug }, "Starting test rerun job");

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({
                jobId: job.id,
                message: `Test rerun job created for ${input.projectSlug}. Use check_status to monitor.`,
              }, null, 2),
            },
          ],
        };
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
