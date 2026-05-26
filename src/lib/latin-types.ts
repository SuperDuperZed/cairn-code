// ============================================================
// Latin Dictionary — Shared Types
// Extractable for React Native: no framework dependencies here
// ============================================================

export type PartOfSpeech =
  | 'noun'
  | 'verb'
  | 'adjective'
  | 'adverb'
  | 'pronoun'
  | 'preposition'
  | 'conjunction'
  | 'interjection'
  | 'numeral'
  | 'particle';

export type Gender = 'masculine' | 'feminine' | 'neuter' | 'common';

export type Frequency = 1 | 2 | 3 | 4 | 5; // 1=most common, 5=rare

export type Declension = 1 | 2 | 3 | 4 | 5;

export type Conjugation = 1 | 2 | 3 | 4;

export interface Example {
  latin: string;
  english: string;
}

export interface NounForms {
  singular: [string, string, string, string, string, string, string]; // nom,gen,dat,acc,voc,abl,loc
  plural: [string, string, string, string, string, string, string];
}

export interface VerbForms {
  indicative: {
    active: [string, string, string, string, string, string]; // pres,impf,fut,perf,plup,futp
    passive: [string, string, string, string, string, string];
  };
  subjunctive: {
    active: [string, string, string, string, string, string];
    passive: [string, string, string, string, string, string];
  };
  infinitives: {
    active: [string, string, string]; // pres, perf, fut
    passive: [string, string, string];
  };
  participles: {
    present: string;
    perfect: string;
    future: string;
    gerund: string;
    supine: string;
  };
  imperatives: {
    present: [string, string]; // sg, pl
    future: [string, string];
  };
}

export interface AdjectiveForms {
  masculine: [string, string, string]; // nom sg, nom pl, gen sg
  feminine: [string, string, string];
  neuter: [string, string, string];
}

export interface LatinWord {
  id: string;
  lemma: string;
  partOfSpeech: PartOfSpeech;
  definitions: string[];
  gender?: Gender;
  declension?: Declension;
  conjugation?: Conjugation;
  principalParts?: string[];
  nounForms?: NounForms;
  verbForms?: VerbForms;
  adjectiveForms?: AdjectiveForms;
  examples: Example[];
  categories: string[];
  etymology?: string;
  frequency: Frequency;
  relatedWords?: string[]; // lemma IDs
  notes?: string;
}

export interface SearchResult {
  word: LatinWord;
  matchType: 'exact' | 'prefix' | 'fuzzy' | 'definition';
  score: number;
}

export type SearchOptions = {
  query: string;
  limit?: number;
  partOfSpeech?: PartOfSpeech[];
  category?: string;
};
