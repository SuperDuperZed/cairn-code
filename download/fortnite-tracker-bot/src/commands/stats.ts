// /stats command — look up a player's Battle Royale stats

import {
  type ChatInputCommandInteraction,
  SlashCommandBuilder,
} from "discord.js";
import { FortniteClient } from "../api/fortnite.ts";
import {
  buildStatsEmbed,
  buildPlayerNotFoundEmbed,
  buildErrorEmbed,
} from "../utils/embeds.ts";

export const name = "stats";

export const data = new SlashCommandBuilder()
  .setName("stats")
  .setDescription("Look up a player's Fortnite BR stats")
  .addStringOption((opt) =>
    opt
      .setName("username")
      .setDescription("Epic Games display name")
      .setRequired(true)
      .setMinLength(3)
      .setMaxLength(32)
  );

export async function execute(
  interaction: ChatInputCommandInteraction,
  client: FortniteClient,
  _clientId: string,
): Promise<void> {
  const username = interaction.options.getString("username", true);

  // Defer reply since API calls take a moment
  await interaction.deferReply();

  try {
    const stats = await client.getStats(username);
    const embed = buildStatsEmbed(stats);
    await interaction.editReply({ embeds: [embed] });
  } catch (err) {
    const msg = (err as Error).message;

    if (msg.includes("not found") || msg.includes("Not Found")) {
      await interaction.editReply({
        embeds: [buildPlayerNotFoundEmbed(username)],
      });
    } else if (msg.includes("Rate limited")) {
      await interaction.editReply({
        embeds: [
          buildErrorEmbed(
            "Rate Limited",
            "The Fortnite API is rate-limited right now. Please try again in a moment.",
          ),
        ],
      });
    } else if (msg.includes("timed out")) {
      await interaction.editReply({
        embeds: [
          buildErrorEmbed(
            "Timeout",
            "The Fortnite API took too long to respond. Try again.",
          ),
        ],
      });
    } else {
      console.error(`[stats] Unexpected error:`, err);
      await interaction.editReply({
        embeds: [
          buildErrorEmbed(
            "Error",
            `Something went wrong while looking up **${username}**.\n\`${msg.slice(0, 200)}\``,
          ),
        ],
      });
    }
  }
}
