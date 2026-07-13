import type { OpportunityType } from "@/types/api";

export const OPPORTUNITY_TYPES: { value: OpportunityType; label: string }[] = [
  { value: "olympiad", label: "Olympiad" },
  { value: "hackathon", label: "Hackathon" },
  { value: "research_program", label: "Research program" },
  { value: "summer_school", label: "Summer school" },
  { value: "competition", label: "Competition" },
  { value: "scholarship", label: "Scholarship" },
  { value: "fellowship", label: "Fellowship" },
];

export function formatOpportunityType(type: OpportunityType): string {
  return OPPORTUNITY_TYPES.find((item) => item.value === type)?.label ?? type;
}

export function formatDeadline(value: string | null): string {
  if (!value) return "No deadline listed";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "No deadline listed";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatGradeRange(
  min: number | null,
  max: number | null,
  fallback: string | null,
): string {
  if (min != null && max != null) return `Grades ${min}–${max}`;
  if (min != null) return `Grade ${min}+`;
  if (max != null) return `Up to grade ${max}`;
  return fallback ?? "Grade not specified";
}
