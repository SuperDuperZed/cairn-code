import { NextResponse } from "next/server";
import { getRandomEvent, weirdEvents } from "@/lib/events";
import { execSync } from "child_process";
import { existsSync } from "fs";
import path from "path";

const EVENTS_DIR = path.join(process.cwd(), "public", "events");

export async function GET() {
  try {
    const event = getRandomEvent();
    const imagePath = path.join(EVENTS_DIR, `${event.slug}.png`);

    // Check if image already exists
    if (!existsSync(imagePath)) {
      // Generate image using z-ai-generate
      const prompt = event.imagePrompt;
      try {
        execSync(
          `z-ai-generate -p "${prompt.replace(/"/g, '\\"')}" -o "${imagePath}" -s 1344x768`,
          {
            timeout: 120000, // 2 minute timeout
            stdio: "pipe",
          }
        );
      } catch (generateError) {
        console.error("Image generation failed:", generateError);
        // Return event without image — frontend will show a placeholder
        return NextResponse.json({
          year: event.year,
          title: event.title,
          description: event.description,
          slug: event.slug,
          imageUrl: null,
          totalEvents: weirdEvents.length,
        });
      }
    }

    return NextResponse.json({
      year: event.year,
      title: event.title,
      description: event.description,
      slug: event.slug,
      imageUrl: `/events/${event.slug}.png`,
      totalEvents: weirdEvents.length,
    });
  } catch (error) {
    console.error("Error in random-event API:", error);
    return NextResponse.json(
      { error: "Failed to generate event" },
      { status: 500 }
    );
  }
}
