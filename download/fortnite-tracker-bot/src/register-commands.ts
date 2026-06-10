// Register slash commands with Discord
// Run once:  deno task register

import { REST, Routes, SlashCommandBuilder } from "discord.js";
import { loadConfig } from "./config.ts";

const config = loadConfig();

const commands = [
  new SlashCommandBuilder()
    .setName("stats")
    .setDescription("Look up a player's Fortnite BR stats")
    .addStringOption((opt) =>
      opt
        .setName("username")
        .setDescription("Epic Games display name")
        .setRequired(true)
        .setMinLength(3)
        .setMaxLength(32)
    )
    .toJSON(),

  new SlashCommandBuilder()
    .setName("shop")
    .setDescription("Show the current Fortnite item shop")
    .toJSON(),

  new SlashCommandBuilder()
    .setName("help")
    .setDescription("Show bot commands and info")
    .toJSON(),
];

const rest = new REST({ version: "10" }).setToken(config.discordToken);

console.log(`[register] Registering ${commands.length} commands...`);

try {
  if (config.guildIds && config.guildIds.length > 0) {
    // Guild-specific registration (instant, great for dev)
    for (const guildId of config.guildIds) {
      await rest.put(
        Routes.applicationGuildCommands(config.clientId, guildId),
        { body: commands },
      );
      console.log(`[register] Registered in guild ${guildId}`);
    }
  } else {
    // Global registration (can take up to 1 hour to propagate)
    await rest.put(Routes.applicationCommands(config.clientId), {
      body: commands,
    });
    console.log("[register] Registered globally (may take up to 1 hour)");
  }
  console.log("[register] Done!");
} catch (err) {
  console.error("[register] Failed:", err);
  Deno.exit(1);
}
