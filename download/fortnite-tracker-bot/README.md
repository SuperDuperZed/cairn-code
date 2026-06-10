# 🎮 Fortnite Tracker Discord Bot

A Deno-powered Discord bot that tracks Fortnite player stats and displays the current item shop.

## Features

- **`/stats <username>`** — Look up a player's Battle Royale stats (wins, K/D, win rate, matches across Solo/Duo/Squad)
- **`/shop`** — View today's featured and daily item shop with prices and rarity
- **`/help`** — Show available commands and an invite link
- Dual API backend — uses **tracker.gg** when an API key is provided, falls back to **fortnite-api.com** (free, no key)
- Rate-limit aware with clean error embeds

## Prerequisites

- [Deno](https://deno.land) 2.x installed
- A [Discord Bot Application](https://discord.com/developers/applications)
  — copy the **Token** and **Application ID**
- (Optional) A [tracker.gg API key](https://developer.tracker.gg)

## Setup

```bash
# 1. Clone or copy the project
cp -r fortnite-tracker-bot/ my-bot && cd my-bot

# 2. Install dependencies
deno install

# 3. Configure environment
cp .env.example .env
# Edit .env — fill in DISCORD_TOKEN and DISCORD_CLIENT_ID at minimum

# 4. Register slash commands
deno task register

# 5. Start the bot
deno task start
```

## Deno Tasks

| Command            | Description                          |
| ------------------ | ------------------------------------ |
| `deno task start`  | Start the bot                        |
| `deno task dev`    | Start with auto-reload on file change |
| `deno task register` | Register slash commands with Discord |

## Permissions

The bot needs these permissions in your server:

- **Send Messages**
- **Embed Links**
- **Use Application Commands**

## Environment Variables

| Variable             | Required | Description                                    |
| -------------------- | -------- | ---------------------------------------------- |
| `DISCORD_TOKEN`      | ✅       | Bot token from Discord Developer Portal        |
| `DISCORD_CLIENT_ID`  | ✅       | Application ID (Client ID) from Dev Portal     |
| `TRN_API_KEY`        | ❌       | tracker.gg API key — enables enhanced stats     |
| `GUILD_IDS`          | ❌       | Comma-separated guild IDs for fast registration |

## Project Structure

```
main.ts                  # Entry point — bot bootstrap & login
src/
  config.ts              # Load env vars
  register-commands.ts   # Slash command registration script
  commands/
    mod.ts               # Command registry
    stats.ts             # /stats command handler
    shop.ts              # /shop command handler
    help.ts              # /help command handler
  api/
    fortnite.ts          # Fortnite API client (dual backend)
  utils/
    embeds.ts            # Discord embed builders
  types.ts               # Shared TypeScript types
```

## License

MIT
