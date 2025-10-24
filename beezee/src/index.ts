import { Hono } from "hono";
import { McpServer, StreamableHttpTransport } from "mcp-lite";
import { z } from "zod";

// TypeScript types for Cloudflare Worker environment
type Env = {
  DB: any; // D1Database type from @cloudflare/workers-types
};

// Factory function to create MCP server with DB access
function createMcpServer(db: any) {
  const mcp = new McpServer({
    name: "cafe-crowd-mcp-server",
    version: "1.0.0",
    schemaAdapter: (schema) => z.toJSONSchema(schema as z.ZodType),
  });

  // Tool 1: Find cafes that are not busy
  mcp.tool("find_quiet_cafes", {
    description: "Find cafes that are currently not busy based on real-time sensor data. Returns cafes with low crowd scores.",
    inputSchema: z.object({
      max_score: z.number().optional().describe("Maximum busyness score (default: 5.0). Lower scores mean less busy."),
      limit: z.number().optional().describe("Maximum number of cafes to return (default: 5)"),
    }),
    handler: async (args) => {
      const maxScore = args.max_score ?? 5.0;
      const limit = args.limit ?? 5;

      // Get the latest reading for each cafe where score is below threshold
      const result = await db.prepare(`
        SELECT name, address, unix_timestamp, normalized_score
        FROM "normalized-score-2"
        WHERE normalized_score <= ?
        AND unix_timestamp = (
          SELECT MAX(unix_timestamp)
          FROM "normalized-score-2" t2
          WHERE t2.name = "normalized-score-2".name
        )
        ORDER BY normalized_score ASC
        LIMIT ?
      `).bind(maxScore, limit).all();

      if (result.results.length === 0) {
        return {
          content: [{
            type: "text",
            text: `No cafes found with busyness score below ${maxScore}. Try increasing the max_score parameter.`
          }]
        };
      }

      const cafes = result.results.map((row: any) => {
        const date = new Date(row.unix_timestamp * 1000);
        return `📍 ${row.name}\n   Address: ${row.address}\n   Busyness Score: ${row.normalized_score.toFixed(2)}/10\n   Last Updated: ${date.toLocaleString()}`;
      }).join("\n\n");

      return {
        content: [{
          type: "text",
          text: `Found ${result.results.length} quiet cafe(s):\n\n${cafes}`
        }]
      };
    },
  });

  // Tool 2: Get current status of a specific cafe
  mcp.tool("get_cafe_status", {
    description: "Get the current busyness status of a specific cafe by name",
    inputSchema: z.object({
      cafe_name: z.string().describe("Name of the cafe (partial match supported)"),
    }),
    handler: async (args) => {
      const result = await db.prepare(`
        SELECT name, address, unix_timestamp, normalized_score
        FROM "normalized-score-2"
        WHERE name LIKE ?
        ORDER BY unix_timestamp DESC
        LIMIT 1
      `).bind(`%${args.cafe_name}%`).all();

      if (result.results.length === 0) {
        return {
          content: [{
            type: "text",
            text: `No cafe found matching "${args.cafe_name}". Try using the list_all_cafes tool to see available cafes.`
          }]
        };
      }

      const cafe: any = result.results[0];
      const date = new Date(cafe.unix_timestamp * 1000);
      const status = cafe.normalized_score < 3 ? "🟢 Quiet" :
                     cafe.normalized_score < 6 ? "🟡 Moderate" : "🔴 Busy";

      return {
        content: [{
          type: "text",
          text: `${status}\n\n📍 ${cafe.name}\n   Address: ${cafe.address}\n   Busyness Score: ${cafe.normalized_score.toFixed(2)}/10\n   Last Updated: ${date.toLocaleString()}`
        }]
      };
    },
  });

  // Tool 3: List all available cafes
  mcp.tool("list_all_cafes", {
    description: "List all cafes in the database with their current busyness status",
    inputSchema: z.object({}),
    handler: async () => {
      // Get latest reading for each unique cafe
      const result = await db.prepare(`
        SELECT DISTINCT name, address,
               (SELECT normalized_score FROM "normalized-score-2" t2
                WHERE t2.name = t1.name ORDER BY unix_timestamp DESC LIMIT 1) as latest_score,
               (SELECT unix_timestamp FROM "normalized-score-2" t2
                WHERE t2.name = t1.name ORDER BY unix_timestamp DESC LIMIT 1) as latest_timestamp
        FROM "normalized-score-2" t1
        ORDER BY latest_score ASC
      `).all();

      if (result.results.length === 0) {
        return {
          content: [{
            type: "text",
            text: "No cafes found in the database."
          }]
        };
      }

      const cafes = result.results.map((row: any) => {
        const status = row.latest_score < 3 ? "🟢" : row.latest_score < 6 ? "🟡" : "🔴";
        return `${status} ${row.name} - Score: ${row.latest_score.toFixed(2)}/10\n   ${row.address}`;
      }).join("\n\n");

      return {
        content: [{
          type: "text",
          text: `All Cafes (${result.results.length}):\n\n${cafes}`
        }]
      };
    },
  });

  return mcp;
}

const app = new Hono<{ Bindings: Env }>();

app.all("/mcp", async (c) => {
  const mcp = createMcpServer(c.env.DB);
  const transport = new StreamableHttpTransport();
  const httpHandler = transport.bind(mcp);
  const response = await httpHandler(c.req.raw);
  return response;
});

app.get("/", (c) => {
  return c.text("Cafe Crowd Recognition MCP Server - Connect to /mcp");
});

export default app;
