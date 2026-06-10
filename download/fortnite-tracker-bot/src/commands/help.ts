// /help command — show available commands and bot info

import { type ChatInputCommandInteraction } from "discord.js";
import { buildHelpEmbed } from "../utils/embeds.ts";

export const name = "help";
export const description = "Show bot commands and info";

export async function execute(
  interaction: ChatInputCommandInteraction,
  clientId: string,
): Promise<void> {
  await interaction.reply({ embeds: [buildHelpEmbed(clientId)] });
}
