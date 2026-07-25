import { ImageResponse } from "next/og";

import { SITE_NAME, SITE_TAGLINE, brandMarkDataUri } from "@/lib/brand";

export const size = { width: 1200, height: 630 };
export const contentType = "image/png";
export const alt = `${SITE_NAME} — ${SITE_TAGLINE}`;

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          width: "100%",
          height: "100%",
          padding: "72px",
          background: "linear-gradient(140deg, #0b1f2a 0%, #0f766e 100%)",
          color: "#f7fbfc",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "24px" }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={brandMarkDataUri} alt="" width={88} height={88} />
          <div style={{ fontSize: 44, fontWeight: 700, letterSpacing: "-0.02em" }}>
            {SITE_NAME}
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <div
            style={{
              fontSize: 68,
              fontWeight: 700,
              lineHeight: 1.1,
              letterSpacing: "-0.03em",
              maxWidth: "900px",
            }}
          >
            {SITE_TAGLINE}
          </div>
          <div style={{ fontSize: 32, color: "#a7e8e0" }}>
            Olympiads · Hackathons · Research · Scholarships
          </div>
        </div>
      </div>
    ),
    size
  );
}
