// Discord embed builders with Fortnite branding

import {
  EmbedBuilder,
  type EmbedField,
  type ColorResolvable,
} from "discord.js";
import { rarityColor, type PlayerStats, type Rarity } from "../types.ts";

// Fortnite brand colors
const FORTNITE_BLUE = 0x0091ff;
const FORTNITE_PURPLE = 0x9b59b6;
const FORTNITE_DARK = 0x2c2f33;

// ── Stats embed ──────────────────────────────────────────────────────────

export function buildStatsEmbed(stats: PlayerStats): EmbedBuilder {
  const winRatePercent = (v: number | null) => v != null ? `${v.toFixed(1)}%` : "N/A";
  const kdStr = (v: number | null) => v != null ? v.toFixed(2) : "N/A";
  const num = (v: number | null) => v != null ? v.toLocaleString() : "N/A";

  const embed = new EmbedBuilder()
    .setTitle(`${stats.displayName || stats.username}`)
    .setURL(
      `https://fortnitetracker.com/profile/all/${encodeURIComponent(stats.username)}`,
    )
    .setColor(FORTNITE_BLUE as ColorResolvable)
    .setThumbnail(
      "https://img.icons8.com/3d-fluency/188/fortnite.png",
    )
    .setFooter({
      text: "Fortnite Tracker Bot",
      iconURL: "https://img.icons8.com/3d-fluency/188/fortnite.png",
    })
    .setTimestamp();

  // Overall stats
  if (stats.overall) {
    const o = stats.overall;
    embed.addFields({
      name: "🏆 Overall",
      value:
        `**Wins:** ${num(o.wins)}  |  **Kills:** ${num(o.kills)}\n` +
        `**K/D:** ${kdStr(o.kd)}  |  **Win Rate:** ${winRatePercent(o.winRate)}\n` +
        `**Matches:** ${num(o.matches)}  |  **Score:** ${num(o.score)}`,
      inline: false,
    });
  }

  // Mode breakdown
  const modes: EmbedField[] = [];

  if (stats.solo) {
    modes.push({
      name: "👤 Solo",
      value:
        `W: ${num(stats.solo.wins)} | K: ${num(stats.solo.kills)}\nK/D: ${kdStr(stats.solo.kd)} | WR: ${winRatePercent(stats.solo.winRate)}`,
      inline: true,
    });
  }
  if (stats.duo) {
    modes.push({
      name: "👥 Duo",
      value:
        `W: ${num(stats.duo.wins)} | K: ${num(stats.duo.kills)}\nK/D: ${kdStr(stats.duo.kd)} | WR: ${winRatePercent(stats.duo.winRate)}`,
      inline: true,
    });
  }
  if (stats.squad) {
    modes.push({
      name: "🏠 Squad",
      value:
        `W: ${num(stats.squad.wins)} | K: ${num(stats.squad.kills)}\nK/D: ${kdStr(stats.squad.kd)} | WR: ${winRatePercent(stats.squad.winRate)}`,
      inline: true,
    });
  }

  if (modes.length > 0) {
    embed.addFields(modes);
  }

  return embed;
}

// ── Stats not found embed ──────────────────────────────────────────────────

export function buildPlayerNotFoundEmbed(username: string): EmbedBuilder {
  return new EmbedBuilder()
    .setTitle("Player Not Found")
    .setDescription(
      `Could not find player **${username}**.\n\n` +
        "Make sure the username matches their Epic Games display name exactly. " +
        "Check for spaces, numbers, and special characters.",
    )
    .setColor(0xe74c3c as ColorResolvable)
    .setTimestamp();
}

// ── Shop embed ─────────────────────────────────────────────────────────────

export function buildShopEmbed(
  data: FortniteAPIShopResponse["data"],
): EmbedBuilder[] {
  const embeds: EmbedBuilder[] = [];

  // Featured items
  if (data.featured.length > 0) {
    const featured = new EmbedBuilder()
      .setTitle("🛒 Featured Items")
      .setColor(FORTNITE_PURPLE as ColorResolvable)
      .setFooter({
        text: `Shop updated: ${data.date}`,
      });

    const items = data.featured.flatMap((entry) => entry.entry.items);
    const uniqueItems = [...new Map(items.map((i) => [i.itemId, i])).values()];

    const MAX_FIELDS = 20;
    for (let i = 0; i < Math.min(uniqueItems.length, MAX_FIELDS); i++) {
      const item = uniqueItems[i];
      const rarity = (item.rarityBackup || item.rarity) as Rarity;
      const emoji = rarityEmoji(rarity);
      const priceStr = item.price > 0
        ? `${item.price.toLocaleString()} `
        : "Free ";

      featured.addFields({
        name: `${emoji} ${item.name}`,
        value:
          `${priceStr}V-Bucks\n${capitalize(rarity)}  ·  ${item.displayAssets[0]?.materialInstance ? `[View](${shopImageUrl(item)})` : "No image"}`,
        inline: true,
      });
    }

    if (uniqueItems.length === 0) {
      featured.setDescription("No featured items right now.");
    }

    embeds.push(featured);
  }

  // Daily items
  if (data.daily.length > 0) {
    const daily = new EmbedBuilder()
      .setTitle("📋 Daily Items")
      .setColor(FORTNITE_BLUE as ColorResolvable)
      .setFooter({
        text: `Shop updated: ${data.date}`,
      });

    const items = data.daily.flatMap((entry) => entry.entry.items);
    const uniqueItems = [...new Map(items.map((i) => [i.itemId, i])).values()];

    for (let i = 0; i < Math.min(uniqueItems.length, MAX_FIELDS); i++) {
      const item = uniqueItems[i];
      const rarity = (item.rarityBackup || item.rarity) as Rarity;
      const emoji = rarityEmoji(rarity);
      const priceStr = item.price > 0
        ? `${item.price.toLocaleString()} `
        : "Free ";

      daily.addFields({
        name: `${emoji} ${item.name}`,
        value:
          `${priceStr}V-Bucks\n${capitalize(rarity)}  ·  ${item.displayAssets[0]?.materialInstance ? `[View](${shopImageUrl(item)})` : "No image"}`,
        inline: true,
      });
    }

    if (uniqueItems.length === 0) {
      daily.setDescription("No daily items right now.");
    }

    embeds.push(daily);
  }

  if (embeds.length === 0) {
    embeds.push(
      new EmbedBuilder()
        .setTitle("Item Shop")
        .setDescription("The shop is currently empty or unavailable.")
        .setColor(FORTNITE_DARK as ColorResolvable),
    );
  }

  return embeds;
}

// ── Help embed ─────────────────────────────────────────────────────────────

export function buildHelpEmbed(clientId: string): EmbedBuilder {
  return new EmbedBuilder()
    .setTitle("Fortnite Tracker Bot")
    .setColor(FORTNITE_BLUE as ColorResolvable)
    .setThumbnail("https://img.icons8.com/3d-fluency/188/fortnite.png")
    .setDescription(
      "Track Fortnite player stats and view the current item shop.",
    )
    .addFields(
      {
        name: " Slash Commands",
        value: "",
        inline: false,
      },
      {
        name: "/stats `<username>`",
        value: "Look up a player's Battle Royale stats including wins, K/D, and win rate.",
        inline: true,
      },
      {
        name: "/shop",
        value: "Show today's featured and daily item shop items with prices.",
        inline: true,
      },
      {
        name: "/help",
        value: "Show this help message.",
        inline: true,
      },
      {
        name: " Invite Link",
        value: "",
        inline: false,
      },
      {
        name: "Add to your server",
        value:
          `https://discord.com/oauth2/authorize?client_id=${clientId}&permissions=274877975552&scope=bot%20applications.commands`,
        inline: true,
      },
    )
    .setFooter({ text: "Built with Deno + discord.js" })
    .setTimestamp();
}

// ── Error embed ───────────────────────────────────────────────────────────

export function buildErrorEmbed(title: string, message: string): EmbedBuilder {
  return new EmbedBuilder()
    .setTitle(title)
    .setDescription(message)
    .setColor(0xe74c3c as ColorResolvable)
    .setTimestamp();
}

// ── Helpers ────────────────────────────────────────────────────────────────

function rarityEmoji(rarity: Rarity): string {
  const map: Record<Rarity, string> = {
    common: "⚪",
    uncommon: "🟢",
    rare: "🔵",
    epic: "🟣",
    legendary: "🟡",
    mythic: "🔴",
    transcendent: "💎",
  };
  return map[rarity] ?? "⚪";
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function shopImageUrl(item: { name: string }): string {
  return `https://fortnite-api.com/images/${encodeURIComponent(item.name)}.png`;
}
