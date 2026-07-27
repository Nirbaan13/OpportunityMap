export const SITE_NAME = "OpportunityMap";

export const SITE_TAGLINE =
  "Find the olympiads, hackathons, and research programs you are actually eligible for.";

export const SITE_URL = (
  process.env.NEXT_PUBLIC_SITE_URL || "https://opportunitymap.info"
).replace(/\/$/, "");
