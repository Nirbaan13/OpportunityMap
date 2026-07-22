export type User = {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
  has_profile: boolean;
  is_premium: boolean;
  premium_until: string | null;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type FieldOption = {
  id: number;
  name: string;
  slug: string;
};

export type ActivityOption = {
  id: number;
  name: string;
  slug: string;
};

export type FieldInsight = {
  field: FieldOption;
  completed_count: number;
  planned_count: number;
  status: "strong" | "ok" | "short" | string;
};

export type Profile = {
  id: number;
  email: string;
  full_name: string;
  location: string;
  grade_level: number;
  country_code: string;
  research_experience: string | null;
  olympiad_experience: string | null;
  interests: FieldOption[];
  completed_activities: ActivityOption[];
  planned_activities: ActivityOption[];
  completed_opportunities: CompletedOpportunityBrief[];
  field_insights: FieldInsight[];
  insight_summary: string;
  created_at: string;
  updated_at: string;
};

export type CompletedOpportunityBrief = {
  id: number;
  title: string;
  opportunity_type: string;
  fields: FieldOption[];
  completed_at: string | null;
};

export type ProfileWriteRequest = {
  full_name: string;
  location: string;
  grade_level: number;
  country_code: string;
  research_experience?: string | null;
  olympiad_experience?: string | null;
  interest_slugs: string[];
  completed_activity_slugs: string[];
  planned_activity_slugs: string[];
};

export type OpportunityType =
  | "olympiad"
  | "hackathon"
  | "research_program"
  | "summer_school"
  | "competition"
  | "scholarship"
  | "fellowship";

export type OpportunitySort = "deadline_asc" | "deadline_desc" | "newest" | "title";

export type OpportunitySummary = {
  id: number;
  title: string;
  opportunity_type: OpportunityType;
  source_name: string;
  source_url: string;
  application_url: string | null;
  deadline_at: string | null;
  grade_eligibility: string | null;
  grade_min: number | null;
  grade_max: number | null;
  eligible_countries: string[] | null;
  is_active: boolean;
  fields: FieldOption[];
};

export type OpportunityDetail = OpportunitySummary & {
  description: string | null;
  experience_requirements: string | null;
  external_id: string | null;
  last_scraped_at: string | null;
  created_at: string;
  updated_at: string;
};

export type OpportunityListResponse = {
  items: OpportunitySummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type OpportunityListParams = {
  q?: string;
  opportunity_type?: OpportunityType;
  field?: string;
  source?: string;
  country?: string;
  grade?: number;
  open_only?: boolean;
  sort?: OpportunitySort;
  page?: number;
  page_size?: number;
};

export type MatchItem = {
  opportunity: OpportunitySummary;
  score: number;
  shared_fields: FieldOption[];
  reasons: string[];
};

export type MatchListResponse = {
  items: MatchItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type MatchListParams = {
  open_only?: boolean;
  opportunity_type?: OpportunityType;
  page?: number;
  page_size?: number;
};

export type BookmarkStatus = "saved" | "completed";

export type BookmarkItem = {
  opportunity: OpportunitySummary;
  remind_me: boolean;
  status: BookmarkStatus;
  completed_at: string | null;
  created_at: string;
};

export type BookmarkListResponse = {
  items: BookmarkItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type BookmarkListParams = {
  page?: number;
  page_size?: number;
  status?: BookmarkStatus;
};

export type NotificationType = "new_match" | "deadline_reminder";

export type NotificationItem = {
  id: number;
  notification_type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  reminder_lead_days: number | null;
  opportunity: OpportunitySummary | null;
  created_at: string;
};

export type NotificationListResponse = {
  items: NotificationItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  unread_count: number;
};

export type NotificationListParams = {
  unread_only?: boolean;
  page?: number;
  page_size?: number;
};

export type PaymentConfig = {
  price_inr: number;
  amount_paise: number;
  currency: string;
  razorpay_enabled: boolean;
  razorpay_key_id: string | null;
  dev_unlock_available: boolean;
  description: string;
};

export type CreateOrderResponse = {
  order_id: string;
  amount_paise: number;
  currency: string;
  key_id: string;
  name: string;
  description: string;
  prefill_email: string;
  payment_id: number;
};

export type PaymentStatus = {
  order_id: string;
  status: "created" | "failed" | "paid" | "refunded";
  is_premium: boolean;
  premium_until: string | null;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}
