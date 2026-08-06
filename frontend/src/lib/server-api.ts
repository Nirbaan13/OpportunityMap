import type { OpportunityDetail, OpportunityListResponse } from "@/types/api";

function resolveApiBaseUrl(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").trim();
  let base = raw || "http://localhost:8000";
  base = base.replace(/\/+$/, "");
  base = base.replace(/\/api\/v1$/i, "");
  if (base && !/^https?:\/\//i.test(base)) {
    base = `https://${base}`;
  }
  return base;
}

const API_URL = resolveApiBaseUrl();

async function serverGet<T>(path: string, init?: RequestInit): Promise<T | null> {
  try {
    const response = await fetch(`${API_URL}/api/v1${path}`, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init?.headers ?? {}),
      },
      // Opportunity pages change as scrapers run; keep metadata reasonably fresh.
      next: { revalidate: 3600 },
    });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function fetchOpportunityForSeo(
  id: number,
): Promise<OpportunityDetail | null> {
  if (!Number.isFinite(id) || id <= 0) return null;
  return serverGet<OpportunityDetail>(`/opportunities/${id}`);
}

export async function fetchOpportunitySitemapEntries(): Promise<
  { id: number }[]
> {
  const pageSize = 100;
  const first = await serverGet<OpportunityListResponse>(
    `/opportunities?page=1&page_size=${pageSize}&sort=newest`,
  );
  if (!first || first.total === 0) return [];

  const totalPages = Math.min(first.total_pages || 1, 50);
  const restPages =
    totalPages > 1
      ? await Promise.all(
          Array.from({ length: totalPages - 1 }, (_, i) =>
            serverGet<OpportunityListResponse>(
              `/opportunities?page=${i + 2}&page_size=${pageSize}&sort=newest`,
            ),
          ),
        )
      : [];

  const entries: { id: number }[] = first.items.map((item) => ({ id: item.id }));
  for (const batch of restPages) {
    if (!batch?.items?.length) continue;
    for (const item of batch.items) {
      entries.push({ id: item.id });
    }
  }

  return entries;
}
