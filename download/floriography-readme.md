# Floriography

*A random flower, its Latin name, and a verse from a real English poem.*

A minimal, meditative web app that pairs a public-domain photograph of a flower with a stanza from a real English poem. Each visit shows a different bloom — press the button, or come back tomorrow.

**Live:** coming soon

## How it works

Every page load picks a random flower from a curated collection of 12 blooms, each paired with:

- A **public-domain photograph** sourced from Wikimedia Commons
- The flower's **common name** and **Latin binomial**
- A **stanza or couplet** from a real English poem referencing that flower, with poet attribution and date

No AI-generated text. No filler. Just flowers and poetry.

## Tech

- **Next.js 16** (TypeScript)
- **Tailwind CSS 4** + **shadcn/ui**
- **Google Fonts**: Playfair Display (serif), Geist (sans + mono)
- **Static images** from Wikimedia Commons — no image generation, no API keys

## Development

```bash
bun install
bun dev
```

Open [localhost:3000](http://localhost:3000). Each refresh gives you a new flower.

## Flowers in the collection

| Flower | Poet | Poem |
|--------|-------|------|
| Daffodil | William Wordsworth | *I Wandered Lonely as a Cloud* (1807) |
| Rose | William Shakespeare | *Romeo and Juliet* (1597) |
| Poppy | John McCrae | *In Flanders Fields* (1915) |
| Sunflower | William Blake | *Ah! Sun-flower* (1794) |
| Lily | William Blake | *The Lily* (1794) |
| Marigold | William Shakespeare | *The Winter's Tale* (1611) |
| Daisy | William Wordsworth | *To the Daisy* (1802) |
| Primrose | William Wordsworth | *Peter Bell* (1819) |
| Cherry Blossom | A.E. Housman | *A Shropshire Lad* (1896) |
| Bluebell | Emily Brontë | (1846) |
| Violet | Christina Rossetti | (1893) |
| Honeysuckle | James Whitcomb Riley | (1883) |

