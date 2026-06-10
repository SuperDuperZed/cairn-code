// Configuration — loaded from environment variables

import "dotenv/config";

export interface BotConfig {
  discordToken: string;
  clientId: string;
  /** Optional: tracker.gg API key for enhanced stats */
  trackerApiKey?: string;
  /** Optional: restrict commands to these guild IDs (empty = global) */
  guildIds?: string[];
}

export function loadConfig(): BotConfig {
  const token = Deno.env.get("DISCORD_TOKEN");
  const clientId = Deno.env.get("DISCORD_CLIENT_ID");
  const trackerKey = Deno.env.get("TRN_API_KEY");
  const guilds = Deno.env.get("GUILD_IDS");

  if (!token) {
    console.error(
      "[config] DISCORD_TOKEN is required. Set it in .env or environment.",
    );
    Deno.exit(1);
  }
  if (!clientId) {
    console.error(
      "[config] DISCORD_CLIENT_ID is required. Set it in .env or environment.",
    );
    Deno.exit(1);
  }

  return {
    discordToken: token,
    clientId,
    trackerApiKey: trackerKey || undefined,
    guildIds: guilds ? guilds.split(",").map((g) => g.trim()) : undefined,
  };
}
