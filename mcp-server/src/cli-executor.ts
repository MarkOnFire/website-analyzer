/**
 * Utility for executing the Python CLI and handling process spawning.
 */

import { spawn, ChildProcess } from "child_process";
import { logger } from "./logger.js";

export interface SpawnResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  signal: string | null;
}

/**
 * Execute Python CLI command and wait for completion.
 * Used for synchronous operations like listing tests/projects.
 */
export async function executePythonCLI(
  args: string[],
  timeoutMs: number = 30000
): Promise<SpawnResult> {
  return new Promise((resolve, reject) => {
    logger.debug({ args }, "Executing Python CLI");

    const childProcess = spawn("python", ["-m", "src.analyzer.cli", ...args], {
      cwd: "/Users/mriechers/Developer/website-analyzer",
      env: { ...process.env },
    });

    let stdout = "";
    let stderr = "";
    let timedOut = false;

    const timeout = setTimeout(() => {
      timedOut = true;
      childProcess.kill("SIGTERM");
      reject(new Error(`CLI command timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    childProcess.stdout?.on("data", (data: Buffer) => {
      stdout += data.toString();
    });

    childProcess.stderr?.on("data", (data: Buffer) => {
      stderr += data.toString();
    });

    childProcess.on("error", (error: Error) => {
      clearTimeout(timeout);
      logger.error({ error, args }, "Failed to spawn Python CLI");
      reject(new Error(`Failed to spawn Python CLI: ${error.message}`));
    });

    childProcess.on("close", (exitCode: number | null, signal: NodeJS.Signals | null) => {
      clearTimeout(timeout);

      if (timedOut) {
        return; // Already rejected
      }

      logger.debug(
        { exitCode, signal, stdoutLength: stdout.length, stderrLength: stderr.length },
        "Python CLI completed"
      );

      resolve({
        stdout,
        stderr,
        exitCode,
        signal,
      });
    });
  });
}

/**
 * Spawn a Python CLI process for async operations.
 * Returns the ChildProcess for tracking and progress parsing.
 */
export function spawnPythonCLI(args: string[]): ChildProcess {
  logger.info({ args }, "Spawning async Python CLI");

  const childProcess = spawn("python", ["-m", "src.analyzer.cli", ...args], {
    cwd: "/Users/mriechers/Developer/website-analyzer",
    env: { ...process.env },
  });

  childProcess.on("error", (error: Error) => {
    logger.error({ error, args }, "Python CLI process error");
  });

  return childProcess;
}

/**
 * Parse progress messages from Python CLI stdout.
 * Expected formats:
 * - "Crawled 5/100 pages..."
 * - "Running test 2/5: test-name"
 * - "Progress: 50%"
 */
export function parseProgress(line: string): {
  current: number;
  total: number;
  message: string;
} | null {
  // Pattern: "Crawled X/Y pages"
  const crawlMatch = line.match(/Crawled (\d+)\/(\d+) pages/i);
  if (crawlMatch) {
    return {
      current: parseInt(crawlMatch[1], 10),
      total: parseInt(crawlMatch[2], 10),
      message: line.trim(),
    };
  }

  // Pattern: "Running test X/Y: name"
  const testMatch = line.match(/Running test (\d+)\/(\d+)/i);
  if (testMatch) {
    return {
      current: parseInt(testMatch[1], 10),
      total: parseInt(testMatch[2], 10),
      message: line.trim(),
    };
  }

  // Pattern: "Progress: X%"
  const percentMatch = line.match(/Progress:\s*(\d+)%/i);
  if (percentMatch) {
    const percent = parseInt(percentMatch[1], 10);
    return {
      current: percent,
      total: 100,
      message: line.trim(),
    };
  }

  return null;
}
