// /shop command — display the current Fortnite item shop

import { type ChatInputCommandInteraction } from "discord.js";
import { FortniteClient } from "../api/fortnite.ts";
import { buildShopEmbed, buildErrorEmbed } from "../utils/embeds.ts";

export const name = "shop";
export const description = "Show the current Fortnite item shop";

export async function execute(
  interaction: ChatInputCommandInteraction,
  client: FortniteClient,
  _clientId: string,
): Promise<void> {
  await interaction.deferReply();

  try {
    const res = await client.getShop();
    const embeds = buildShopEmbed(res.data);
    await interaction.editReply({ embeds });
  } catch (err) {
    const msg = (err as Error).message;
    console.error(`[shop] Error:`, err);

    await interaction.editReply({
      embeds: [
        buildErrorEmbed(
          "Shop Unavailable",
          msg.includes("timed out")
            ? "The Fortnite API timed out. Try again shortly."
            : `Could not load the item shop.\n\`${msg.slice(0, 200)}\``,
        ),
      ],
    });
  }
}
