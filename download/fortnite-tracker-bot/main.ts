// Fortnite Tracker Discord Bot — Entry point
// Run with:  deno task start

import {
  Client,
  Events,
  GatewayIntentBits,
  type Interaction,
} from "discord.js";
import { loadConfig } from "./src/config.ts";
import { FortniteClient } from "./src/api/fortnite.ts";
import { getCommand } from "./src/commands/mod.ts";

// ── Bootstrap ───────────────────────────────────────────────────────────────

const config = loadConfig();
const fortnite = new FortniteClient({
  trackerApiKey: config.trackerApiKey,
  timeout: 10_000,
});

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    // No message intents needed — we only use slash commands
  ],
});

client.once(Events.ClientReady, (c) => {
  console.log(`[bot] Logged in as ${c.user.tag} (${c.user.id})`);
  console.log(
    `[bot] Serving ${c.guilds.cache.size} guild(s) — /help for commands`,
  );
});

client.on(Events.InteractionCreate, async (interaction: Interaction) => {
  // Only handle slash commands
  if (!interaction.isChatInputCommand()) return;

  const commandName = interaction.commandName;
  const handler = getCommand(commandName);

  if (!handler) {
    console.warn(`[bot] Unknown command: ${commandName}`);
    await interaction.reply({
      content: `Unknown command: \`/${commandName}\``,
      ephemeral: true,
    });
    return;
  }

  try {
    await handler.execute(interaction, fortnite, config.clientId);
  } catch (err) {
    console.error(`[bot] Error executing /${commandName}:`, err);

    // If the interaction hasn't been replied to or deferred, reply with error
    if (interaction.replied || interaction.deferred) {
      await interaction.followUp({
        content: "An unexpected error occurred while running that command.",
        ephemeral: true,
      });
    } else {
      await interaction.reply({
        content: "An unexpected error occurred.",
        ephemeral: true,
      });
    }
  }
});

// ── Login ─────────────────────────────────────────────────────────────────

client.login(config.discordToken).catch((err) => {
  console.error("[bot] Login failed:", err.message);
  Deno.exit(1);
});
