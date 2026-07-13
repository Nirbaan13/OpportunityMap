"use client";

import { FormEvent, useEffect, useState } from "react";

import { SelectField, TextArea, TextField } from "@/components/FormFields";
import { api } from "@/lib/api";
import { ApiError, type ActivityOption, type FieldOption, type Profile } from "@/types/api";

type ProfileFormProps = {
  token: string;
  existing: Profile | null;
  onSaved: (profile: Profile) => void;
};

export function ProfileForm({ token, existing, onSaved }: ProfileFormProps) {
  const [fields, setFields] = useState<FieldOption[]>([]);
  const [activities, setActivities] = useState<ActivityOption[]>([]);
  const [fullName, setFullName] = useState(existing?.full_name ?? "");
  const [location, setLocation] = useState(existing?.location ?? "");
  const [gradeLevel, setGradeLevel] = useState(existing?.grade_level ?? 11);
  const [countryCode, setCountryCode] = useState(existing?.country_code ?? "");
  const [research, setResearch] = useState(existing?.research_experience ?? "");
  const [olympiad, setOlympiad] = useState(existing?.olympiad_experience ?? "");
  const [interestSlugs, setInterestSlugs] = useState<string[]>(
    existing?.interests.map((f) => f.slug) ?? [],
  );
  const [activitySlugs, setActivitySlugs] = useState<string[]>(
    existing?.completed_activities.map((a) => a.slug) ?? [],
  );
  const [loadingOptions, setLoadingOptions] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [fieldList, activityList] = await Promise.all([
          api.listFields(),
          api.listActivities(),
        ]);
        if (!cancelled) {
          setFields(fieldList);
          setActivities(activityList);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load options.");
        }
      } finally {
        if (!cancelled) setLoadingOptions(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  function toggleSlug(
    slug: string,
    current: string[],
    setter: (next: string[]) => void,
  ) {
    setter(
      current.includes(slug)
        ? current.filter((item) => item !== slug)
        : [...current, slug],
    );
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (interestSlugs.length === 0) {
      setError("Pick at least one interest.");
      return;
    }

    const payload = {
      full_name: fullName.trim(),
      location: location.trim(),
      grade_level: gradeLevel,
      country_code: countryCode.trim().toUpperCase(),
      research_experience: research.trim() || null,
      olympiad_experience: olympiad.trim() || null,
      interest_slugs: interestSlugs,
      completed_activity_slugs: activitySlugs,
    };

    setSaving(true);
    try {
      const profile = existing
        ? await api.updateProfile(token, payload)
        : await api.createProfile(token, payload);
      onSaved(profile);
      setSuccess(existing ? "Profile updated." : "Profile created.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save profile.");
    } finally {
      setSaving(false);
    }
  }

  if (loadingOptions) {
    return <p className="text-ink-soft">Loading profile options…</p>;
  }

  return (
    <form onSubmit={onSubmit} className="space-y-8">
      <section className="grid gap-5 sm:grid-cols-2">
        <TextField
          label="Full name"
          name="full_name"
          required
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          autoComplete="name"
        />
        <TextField
          label="Location"
          name="location"
          required
          placeholder="Mumbai, India"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <SelectField
          label="Grade"
          name="grade_level"
          value={gradeLevel}
          onChange={(e) => setGradeLevel(Number(e.target.value))}
        >
          {Array.from({ length: 7 }, (_, i) => i + 6).map((grade) => (
            <option key={grade} value={grade}>
              Grade {grade}
            </option>
          ))}
        </SelectField>
        <TextField
          label="Country code"
          name="country_code"
          required
          minLength={2}
          maxLength={2}
          placeholder="IN"
          value={countryCode}
          onChange={(e) => setCountryCode(e.target.value.toUpperCase())}
        />
      </section>

      <section>
        <h2 className="font-display text-lg font-semibold text-ink">Interests</h2>
        <p className="mt-1 text-sm text-ink-soft">Choose topics you want opportunities in.</p>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {fields.map((field) => {
            const checked = interestSlugs.includes(field.slug);
            return (
              <label
                key={field.slug}
                className={`flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2.5 text-sm transition ${
                  checked
                    ? "border-accent bg-accent/10 text-ink"
                    : "border-line bg-paper text-ink-soft hover:border-accent/40"
                }`}
              >
                <input
                  type="checkbox"
                  className="accent-accent"
                  checked={checked}
                  onChange={() => toggleSlug(field.slug, interestSlugs, setInterestSlugs)}
                />
                {field.name}
              </label>
            );
          })}
        </div>
      </section>

      <section>
        <h2 className="font-display text-lg font-semibold text-ink">What you have done</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Tick activities you have already completed.
        </p>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {activities.map((activity) => {
            const checked = activitySlugs.includes(activity.slug);
            return (
              <label
                key={activity.slug}
                className={`flex cursor-pointer items-center gap-3 rounded-md border px-3 py-2.5 text-sm transition ${
                  checked
                    ? "border-warm/60 bg-warm/10 text-ink"
                    : "border-line bg-paper text-ink-soft hover:border-warm/40"
                }`}
              >
                <input
                  type="checkbox"
                  className="accent-warm"
                  checked={checked}
                  onChange={() => toggleSlug(activity.slug, activitySlugs, setActivitySlugs)}
                />
                {activity.name}
              </label>
            );
          })}
        </div>
      </section>

      <section className="grid gap-5">
        <TextArea
          label="Research experience"
          name="research_experience"
          hint="Optional — a short note helps matching later."
          value={research}
          onChange={(e) => setResearch(e.target.value)}
        />
        <TextArea
          label="Olympiad experience"
          name="olympiad_experience"
          hint="Optional — contests, camps, rankings."
          value={olympiad}
          onChange={(e) => setOlympiad(e.target.value)}
        />
      </section>

      {error ? <p className="text-sm text-danger">{error}</p> : null}
      {success ? <p className="text-sm text-accent">{success}</p> : null}

      <button
        type="submit"
        disabled={saving}
        className="inline-flex items-center rounded-md bg-ink px-5 py-3 text-sm font-semibold text-paper transition hover:bg-ink-soft disabled:opacity-60"
      >
        {saving ? "Saving…" : existing ? "Save changes" : "Create profile"}
      </button>
    </form>
  );
}
