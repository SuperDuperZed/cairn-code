// Fortnite API client — supports multiple backends
// Primary:  fortnite-api.com  (free, no key)
// Optional: tracker.gg        (requires TRN-Api-Key)

import type {
  FortniteAPIStatsResponse,
  PlayerStats,
  FortniteAPIShopResponse,
  TrackerProfileResponse,
} from "../types.ts";

// ---------------------------------------------------------------------------
// Config
// ---------------------------------------------------------------------------

export interface FortniteAPIConfig {
  /** tracker.gg API key (optional, enables TRN backend) */
  trackerApiKey?: string;
  /** Timeout for all HTTP requests in ms */
  timeout?: number;
}

const DEFAULT_TIMEOUT = 8_000;

// ---------------------------------------------------------------------------
// Error helpers
// ---------------------------------------------------------------------------

export class FortniteAPIError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "FortniteAPIError";
  }
}

class PlayerNotFoundError extends FortniteAPIError {
  constructor(username: string) {
    super(404, `Player "${username}" not found`);
    this.name = "PlayerNotFoundError";
  }
}

class RateLimitError extends FortniteAPIError {
  constructor(retryAfter?: number) {
    super(429, `Rate limited. Retry after ${retryAfter ?? "a while"}.`);
    this.name = "RateLimitError";
  }
}

// ---------------------------------------------------------------------------
// HTTP helper
// ---------------------------------------------------------------------------

async function fetchJSON<T>(
  url: string,
  opts: RequestInit & { signal?: AbortSignal; headers?: Record<string, string> } = {},
  timeout = DEFAULT_TIMEOUT,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const res = await fetch(url, {
      ...opts,
      signal: opts.signal ?? controller.signal,
      headers: {
        "Accept": "application/json",
        ...opts.headers,
      },
    });

    if (!res.ok) {
      if (res.status === 429) {
        throw new RateLimitError(
          Number(res.headers.get("Retry-After")) ?? undefined,
        );
      }
      if (res.status === 404) {
        throw new PlayerNotFoundError(
          new URL(url).searchParams.get("name") ?? "unknown",
        );
      }
      const body = await res.text().catch(() => "no body");
      throw new FortniteAPIError(
        res.status,
        `API error ${res.status}: ${body.slice(0, 200)}`,
      );
    }

    return await res.json() as T;
  } catch (err) {
    if (err instanceof FortniteAPIError) throw err;
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new FortniteAPIError(0, "Request timed out");
    }
    throw new FortniteAPIError(0, `Network error: ${(err as Error).message}`);
  } finally {
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// Backend 1 — fortnite-api.com  (free)
// ---------------------------------------------------------------------------

function extractStats(raw: FortniteAPIStatsResponse): PlayerStats {
  const d = raw.data;
  const pick = (
    s: BattleStats | null,
  ) =>
    s
      ? {
        wins: s.wins ?? 0,
        kills: s.kills ?? 0,
        kd: s.kd ?? 0,
        matches: s.matches ?? 0,
        winRate: s.winRate ?? 0,
      }
      : null;

  const overall = d.all.overall
    ? {
      wins: d.all.overall.wins ?? 0,
      kills: d.all.overall.kills ?? 0,
      kd: d.all.overall.kd ?? 0,
      matches: d.all.overall.matches ?? 0,
      winRate: d.all.overall.winRate ?? 0,
      score: d.all.overall.score ?? 0,
      minutesPlayed: d.all.overall.minutesPlayed ?? 0,
    }
    : null;

  return {
    username: d.account.name,
    displayName: d.account.displayName,
    overall,
    solo: pick(d.all.solo),
    duo: pick(d.all.duo),
    squad: pick(d.all.squad),
  };
}

async function fetchStatsFree(username: string): Promise<PlayerStats> {
  const url =
    `https://fortnite-api.com/v2/stats/br/v2?name=${encodeURIComponent(username)}&image=all`;
  const raw = await fetchJSON<FortniteAPIStatsResponse>(url);
  return extractStats(raw);
}

// ---------------------------------------------------------------------------
// Backend 2 — tracker.gg  (requires API key)
// ---------------------------------------------------------------------------

async function fetchStatsTracker(
  username: string,
  apiKey: string,
  platform = "epic",
): Promise<PlayerStats> {
  const url =
    `https://public-api.tracker.gg/v2/fortnite/profile/${platform}/${encodeURIComponent(username)}`;
  const raw = await fetchJSON<TrackerProfileResponse>(url, {
    headers: { "TRN-Api-Key": apiKey },
  });

  const d = raw.data;
  const segments = d.segments;

  // tracker.gg returns multiple segment objects; we need to extract overall/solo/duo/squad
  const findSegment = (type: string) =>
    segments.find((s) => s.type === type);

  const parseStats = (seg?: TrackerSegment) => {
    if (!seg) return null;
    const get = (name: string) => {
      const s = seg.stats.find((st) => st.name === name);
      return s?.value ?? 0;
    };
    return {
      wins: get("matchesWon"),
      kills: get("kills"),
      kd: get("k_d"),
      matches: get("matchesPlayed"),
      winRate: get("winRate"),
      score: 0,
      minutesPlayed: 0,
    };
  };

  const parseMode = (seg?: TrackerSegment) => {
    if (!seg) return null;
    const get = (name: string) => {
      const s = seg.stats.find((st) => st.name === name);
      return s?.value ?? 0;
    };
    return {
      wins: get("matchesWon"),
      kills: get("kills"),
      kd: get("k_d"),
      matches: get("matchesPlayed"),
      winRate: get("winRate"),
    };
  };

  return {
    username: d.platformInfo.platformUserHandle,
    displayName: d.platformInfo.platformUserHandle,
    overall: parseStats(findSegment("overview")),
    solo: parseMode(segments.find((s) => s.type === "mode_solo")),
    duo: parseMode(segments.find((s) => s.type === "mode_duo")),
    squad: parseMode(segments.find((s) => s.type === "mode_squad")),
  };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export class FortniteClient {
  private trackerApiKey?: string;
  private timeout: number;

  constructor(config: FortniteAPIConfig = {}) {
    this.trackerApiKey = config.trackerApiKey;
    this.timeout = config.timeout ?? DEFAULT_TIMEOUT;
  }

  /** Fetch BR stats for a player */
  async getStats(username: string): Promise<PlayerStats> {
    // Prefer tracker.gg if key is available (more accurate)
    if (this.trackerApiKey) {
      try {
        return await fetchStatsTracker(username, this.trackerApiKey);
      } catch (err) {
        if (err instanceof PlayerNotFoundError) throw err;
        console.warn(
          `[fortnite] tracker.gg failed, falling back to free API: ${(err as Error).message}`,
        );
      }
    }
    return await fetchStatsFree(username);
  }

  /** Fetch current item shop */
  async getShop(): Promise<FortniteAPIShopResponse> {
    const url = "https://fortnite-api.com/v2/shop/br";
    return fetchJSON<FortniteAPIShopResponse>(url);
  }
}
