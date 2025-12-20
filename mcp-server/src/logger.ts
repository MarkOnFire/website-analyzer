/**
 * Logging configuration using pino.
 *
 * IMPORTANT: Logs go to stderr because stdout is reserved for the MCP protocol.
 */

import { pino } from "pino";

// Create logger that writes to stderr (fd 2)
export const logger = pino(
  {
    name: "website-analyzer-mcp",
    level: process.env.LOG_LEVEL || "info",
  },
  pino.destination(2) // stderr
);

export default logger;
