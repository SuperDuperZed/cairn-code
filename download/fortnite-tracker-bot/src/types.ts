// Types for the Fortnite API client supporting multiple backends

/** Raw stats from fortnite-api.com /v2/stats/br/v2 */
export interface FortniteAPIStatsResponse {
  status: number;
  data: {
    type: string;
    account: {
      id: string;
      name: string;
      displayName: string;
    };
    battles: {
      solo: null | BattleStats;
      duo: null | BattleStats;
      squad: null | BattleStats;
      trio: null | BattleStats;
      lt: null | BattleStats;
      ltm: null | BattleStats;
    };
    all: {
      overall: null | BattleStats;
      solo: null | BattleStats;
      duo: null | BattleStats;
      squad: null | BattleStats;
      trio: null | BattleStats;
      lt: null | BattleStats;
      ltm: null | BattleStats;
    };
  };
}

export interface BattleStats {
  score: number | null;
  scorePerMin: number | null;
  scorePerMatch: number | null;
  wins: number | null;
  top3: number | null;
  top5: number | null;
  top6: number | null;
  top10: number | null;
  top12: number | null;
  top25: number | null;
  kills: number | null;
  killsPerMin: number | null;
  killsPerMatch: number | null;
  deaths: number | null;
  kd: number | null;
  kpg: number | null;
  matches: number | null;
  winRate: number | null;
  minutesPlayed: number | null;
  playersOutlived: number | null;
  lastModified: string | null;
}

/** Simplified stats for display */
export interface PlayerStats {
  username: string;
  displayName: string;
  overall: {
    wins: number;
    kills: number;
    kd: number;
    matches: number;
    winRate: number;
    score: number;
    minutesPlayed: number;
  } | null;
  solo: {
    wins: number;
    kills: number;
    kd: number;
    matches: number;
    winRate: number;
  } | null;
  duo: {
    wins: number;
    kills: number;
    kd: number;
    matches: number;
    winRate: number;
  } | null;
  squad: {
    wins: number;
    kills: number;
    kd: number;
    matches: number;
    winRate: number;
  } | null;
}

/** Tracker.gg API response for profile search */
export interface TrackerProfileResponse {
  data: {
    platformInfo: {
      platformSlug: string;
      platformUserHandle: string;
      avatarUrl: string;
      additionalUserInfo?: {
          isAnonymous: boolean;
            };
    };
    segments: TrackerSegment[];
  };
  metadata?: Record<string, unknown>;
}

export interface TrackerSegment {
  type: string;
  stats: {
    name: string;
    displayValue: string;
    value: number;
    percentile?: number;
    rank?: string;
  }[];
}

/** Shop item from fortnite-api.com */
export interface FortniteAPIShopResponse {
  status: number;
  data: {
    hash: string;
    date: string;
    featured: ShopFeaturedEntry[];
    daily: ShopFeaturedEntry[];
    specialFeatured: ShopFeaturedEntry[];
    specialDaily: ShopFeaturedEntry[];
  };
}

export interface ShopFeaturedEntry {
  entry: {
    items: ShopItem[];
    new: boolean;
    bundle: null | {
      name: string;
      info: string;
      image: string;
    };
  };
}

export interface ShopItem {
  type: string;
  name: string;
  rarity: Rarity;
  description: string;
  images: {
    icon: string;
    featured: string | null;
    background: string | null;
  };
  displayAssets: {
    materialInstance: string;
  }[];
  price: number;
  offerId: string;
  rarityBackup: Rarity;
  set: string | null;
  setId: string | null;
  addToSet: boolean;
  banner: null | {
    id: string;
    name: string;
    intensity: string;
    alignment: string;
  };
  itemId: string;
}

export type Rarity =
  | "common"
  | "uncommon"
  | "rare"
  | "epic"
  | "legendary"
  | "mythic"
  | "transcendent";

export const RARITY_COLORS: Record<Rarity | "unknown", number> = {
  common: 0xbcbcbc,
  uncommon: 0x5cb85c,
  rare: 0x337ab7,
  epic: 0x9b59b6,
  legendary: 0xf39c12,
  mythic: 0xe74c3c,
  transcendent: 0x00d4aa,
  unknown: 0x99aab5,
};

export function rarityColor(r: Rarity | string): number {
  return RARITY_COLORS[r as Rarity] ?? RARITY_COLORS["unknown"];
}
