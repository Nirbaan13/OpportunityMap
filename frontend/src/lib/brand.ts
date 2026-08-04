export const SITE_NAME = "OpportunityMap";

export const SITE_TAGLINE =
  "Find the olympiads, hackathons, and research programs you are actually eligible for.";

export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL || "https://opportunitymap.info"
).replace(/\/$/, "");

/** Instagram or YouTube tutorial — replace with your video URL when ready. */
export const TUTORIAL_VIDEO_URL =
  process.env.NEXT_PUBLIC_TUTORIAL_VIDEO_URL ||
  "https://www.youtube.com/watch?v=REPLACE_ME";
