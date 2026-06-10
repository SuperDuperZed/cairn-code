// Command registry — maps slash command names to handlers

import { type ChatInputCommandInteraction } from "discord.js";
import { FortniteClient } from "../api/fortnite.ts";
import { execute as statsExecute } from "./stats.ts";
import { execute as shopExecute } from "./shop.ts";
import { execute as helpExecute } from "./help.ts";

export type CommandExecuteFn = (
  interaction: ChatInputCommandInteraction,
  client: FortniteClient,
  clientId: string,
) => Promise<void>;

export interface CommandHandler {
  execute: CommandExecuteFn;
}

/** Map of command name → handler */
const commands: Map<string, CommandHandler> = new Map([
  ["stats", { execute: statsExecute as CommandExecuteFn }],
  ["shop", { execute: shopExecute as CommandExecuteFn }],
  ["help", { execute: helpExecute as CommandExecuteFn }],
]);

export function getCommand(
  name: string,
): CommandHandler | undefined {
  return commands.get(name);
}

export function getAllCommandNames(): string[] {
  return [...commands.keys()];
}
