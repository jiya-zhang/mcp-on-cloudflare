import { Hono } from "hono";
import { McpServer, StreamableHttpTransport } from "mcp-lite";
import { z } from "zod";

// Define the environment interface for D1 binding
interface Env {
  DB: D1Database;
}

const mcp = new McpServer({
  name: "starter-mcp-lite-server",
  version: "1.0.0",
  schemaAdapter: (schema) => z.toJSONSchema(schema as z.ZodType),
});

mcp.tool("query_database", {
  description: "Query the D1 database",
  inputSchema: z.object({
    sql: z.string().describe("SQL query to execute"),
  }),
  handler: async (args, { env }: { env: Env }) => {
    try {
      const result = await env.DB.prepare(args.sql).all();
      return {
        content: [{ 
          type: "text", 
          text: JSON.stringify(result, null, 2) 
        }],
      };
    } catch (error) {
      return {
        content: [{ 
          type: "text", 
          text: `Database error: ${error.message}` 
        }],
      };
    }
  },
});

const transport = new StreamableHttpTransport();
const httpHandler = transport.bind(mcp);

const app = new Hono<{ Bindings: Env }>();

app.all("/mcp", async (c) => {
  // original
  // const response = await httpHandler(c.req.raw, { env: c.env });
  
  // c.env.DB is your D1 database connection
  const response = await c.env.DB.prepare("SELECT DISTINCT(name) FROM normalized-score-2").all();
  return response;
});

app.get("/", (c) => {
  return c.text("Welcome to Beezee!!!");
});

export default app;
