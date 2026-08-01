import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { SITE_NAME, SITE_URL } from "@/lib/brand";
import {
  formatDeadline,
  formatOpportunityType,
} from "@/lib/opportunity-labels";
import { fetchOpportunityForSeo } from "@/lib/server-api";

import { OpportunityDetailClient } from "./OpportunityDetailClient";

type PageProps = {
  params: Promise<{ id: string }>;
};

function truncate(text: string, max: number): string {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (cleaned.length <= max) return cleaned;
  return `${cleaned.slice(0, max - 1).trimEnd()}…`;
}

function buildDescription(opportunity: NonNullable<
  Awaited<ReturnType<typeof fetchOpportunityForSeo>>
>): string {
  const typeLabel = formatOpportunityType(opportunity.opportunity_type);
  const deadline = formatDeadline(opportunity.deadline_at);
  const bits = [
    `${typeLabel} on OpportunityMap`,
    `Deadline: ${deadline}`,
    opportunity.source_name ? `Source: ${opportunity.source_name}` : null,
  ].filter(Boolean);
  const lead = bits.join(" · ");
  if (opportunity.description?.trim()) {
    return truncate(`${lead}. ${opportunity.description.trim()}`, 160);
  }
  return truncate(
    `${lead}. Check eligibility, turn on free Remind me, and apply.`,
    160,
  );
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id: rawId } = await params;
  const id = Number(rawId);
  const opportunity = await fetchOpportunityForSeo(id);

  if (!opportunity) {
    return {
      title: "Opportunity not found",
      robots: { index: false, follow: false },
    };
  }

  const title = opportunity.title;
  const description = buildDescription(opportunity);
  const url = `${SITE_URL}/opportunities/${opportunity.id}`;

  return {
    title,
    description,
    alternates: { canonical: `/opportunities/${opportunity.id}` },
    openGraph: {
      type: "website",
      url,
      siteName: SITE_NAME,
      title: `${title} · ${SITE_NAME}`,
      description,
    },
    twitter: {
      card: "summary_large_image",
      title: `${title} · ${SITE_NAME}`,
      description,
    },
  };
}

export default async function OpportunityDetailPage({ params }: PageProps) {
  const { id: rawId } = await params;
  const id = Number(rawId);
  if (!Number.isFinite(id) || id <= 0) notFound();

  const opportunity = await fetchOpportunityForSeo(id);
  if (!opportunity) notFound();

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebPage",
    name: opportunity.title,
    description: buildDescription(opportunity),
    url: `${SITE_URL}/opportunities/${opportunity.id}`,
    isPartOf: {
      "@type": "WebSite",
      name: SITE_NAME,
      url: SITE_URL,
    },
    about: {
      "@type": "EducationalOccupationalProgram",
      name: opportunity.title,
      provider: opportunity.source_name
        ? { "@type": "Organization", name: opportunity.source_name }
        : undefined,
      url: opportunity.application_url || opportunity.source_url,
    },
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <OpportunityDetailClient
        opportunityId={opportunity.id}
        initialOpportunity={opportunity}
      />
    </>
  );
}
