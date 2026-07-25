import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/brand";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/profile", "/bookmarks", "/notifications"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
