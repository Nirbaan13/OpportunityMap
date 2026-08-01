import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/brand";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: [
        "/profile",
        "/bookmarks",
        "/reminders",
        "/notifications",
        "/admin",
        "/roadmap",
      ],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
