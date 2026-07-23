import {
  ActivityOption,
  ApiError,
  BookmarkItem,
  BookmarkListParams,
  BookmarkListResponse,
  CreateOrderResponse,
  FieldOption,
  MatchListParams,
  MatchListResponse,
  NotificationItem,
  NotificationListParams,
  NotificationListResponse,
  OpportunityDetail,
  OpportunityListParams,
  OpportunityListResponse,
  PaymentConfig,
  PaymentStatus,
  Profile,
  ProfileWriteRequest,
  TokenResponse,
  User,
} from "@/types/api";

function toQuery(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

function resolveApiBaseUrl(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").trim();
  // Empty string is not nullish — without this, fetch becomes relative `/api/v1/...` on the frontend → 404
  let base = raw || "http://localhost:8000";
  base = base.replace(/\/+$/, "");
  // If someone pasted the health/docs path or included /api/v1, strip it
  base = base.replace(/\/api\/v1$/i, "");
  // Host without scheme is treated as a path by fetch → site/opportunitymap-api.../api/v1 → 404
  if (base && !/^https?:\/\//i.test(base)) {
    base = `https://${base}`;
  }
  return base;
}

const API_URL = resolveApiBaseUrl();

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);
  const url = `${API_URL}/api/v1${path}`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: options.method ?? "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(408, "Request timed out. Is the API running?");
    }
    throw err;
  }
  clearTimeout(timeoutId);

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data = (await response.json()) as { detail?: unknown };
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
        message = String(data.detail[0].msg);
      }
    } catch {
      // keep default message
    }
    if (response.status === 404) {
      message = `${message}. Check NEXT_PUBLIC_API_URL (called ${url})`;
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  register(email: string, password: string) {
    return request<User>("/auth/register", {
      method: "POST",
      body: { email, password },
    });
  },

  login(email: string, password: string) {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
    });
  },

  me(token: string) {
    return request<User>("/auth/me", { token });
  },

  setAutoRenew(token: string, autoRenew: boolean) {
    return request<User>("/auth/me/auto-renew", {
      method: "PATCH",
      token,
      body: { auto_renew: autoRenew },
    });
  },

  listFields() {
    return request<FieldOption[]>("/fields");
  },

  listActivities() {
    return request<ActivityOption[]>("/activities");
  },

  getProfile(token: string) {
    return request<Profile>("/profiles/me", { token });
  },

  createProfile(token: string, payload: ProfileWriteRequest) {
    return request<Profile>("/profiles/me", {
      method: "POST",
      token,
      body: payload,
    });
  },

  updateProfile(token: string, payload: ProfileWriteRequest) {
    return request<Profile>("/profiles/me", {
      method: "PUT",
      token,
      body: payload,
    });
  },

  listOpportunities(params: OpportunityListParams = {}) {
    return request<OpportunityListResponse>(
      `/opportunities${toQuery({
        q: params.q,
        opportunity_type: params.opportunity_type,
        field: params.field,
        source: params.source,
        country: params.country,
        grade: params.grade,
        open_only: params.open_only,
        sort: params.sort,
        page: params.page,
        page_size: params.page_size,
      })}`,
    );
  },

  getOpportunity(id: number) {
    return request<OpportunityDetail>(`/opportunities/${id}`);
  },

  listMatches(token: string, params: MatchListParams = {}) {
    return request<MatchListResponse>(
      `/matches${toQuery({
        open_only: params.open_only,
        opportunity_type: params.opportunity_type,
        page: params.page,
        page_size: params.page_size,
      })}`,
      { token },
    );
  },

  listBookmarks(token: string, params: BookmarkListParams = {}) {
    return request<BookmarkListResponse>(
      `/bookmarks${toQuery({
        page: params.page,
        page_size: params.page_size,
        status: params.status,
      })}`,
      { token },
    );
  },

  getBookmark(token: string, opportunityId: number) {
    return request<BookmarkItem>(`/bookmarks/${opportunityId}`, { token });
  },

  addBookmark(token: string, opportunityId: number, remindMe = false) {
    return request<BookmarkItem>("/bookmarks", {
      method: "POST",
      token,
      body: { opportunity_id: opportunityId, remind_me: remindMe, status: "saved" },
    });
  },

  setRemindMe(token: string, opportunityId: number, remindMe: boolean) {
    return request<BookmarkItem>(`/bookmarks/${opportunityId}`, {
      method: "PATCH",
      token,
      body: { remind_me: remindMe },
    });
  },

  setBookmarkStatus(token: string, opportunityId: number, status: "saved" | "completed") {
    return request<BookmarkItem>(`/bookmarks/${opportunityId}`, {
      method: "PATCH",
      token,
      body: { status },
    });
  },

  removeBookmark(token: string, opportunityId: number) {
    return request<void>(`/bookmarks/${opportunityId}`, {
      method: "DELETE",
      token,
    });
  },

  listNotifications(token: string, params: NotificationListParams = {}) {
    return request<NotificationListResponse>(
      `/notifications${toQuery({
        unread_only: params.unread_only,
        page: params.page,
        page_size: params.page_size,
      })}`,
      { token },
    );
  },

  unreadNotificationCount(token: string) {
    return request<{ unread_count: number }>("/notifications/unread-count", { token });
  },

  markNotificationRead(token: string, notificationId: number) {
    return request<NotificationItem>(`/notifications/${notificationId}/read`, {
      method: "POST",
      token,
    });
  },

  markAllNotificationsRead(token: string) {
    return request<{ unread_count: number }>("/notifications/read-all", {
      method: "POST",
      token,
    });
  },

  paymentConfig() {
    return request<PaymentConfig>("/payments/config");
  },

  createPaymentOrder(token: string, currency: "INR" = "INR") {
    return request<CreateOrderResponse>("/payments/create-order", {
      method: "POST",
      token,
      body: { currency },
    });
  },

  createPolarCheckout(token: string) {
    return request<{ checkout_url: string }>("/payments/polar/create-checkout", {
      method: "POST",
      token,
    });
  },

  verifyPayment(
    token: string,
    payload: {
      razorpay_order_id: string;
      razorpay_payment_id: string;
      razorpay_signature: string;
    },
  ) {
    return request<User>("/payments/verify", {
      method: "POST",
      token,
      body: payload,
    });
  },

  paymentStatus(token: string, orderId: string) {
    return request<PaymentStatus>(`/payments/status/${encodeURIComponent(orderId)}`, {
      token,
    });
  },

  devUnlockPremium(token: string) {
    return request<User>("/payments/dev-unlock", {
      method: "POST",
      token,
    });
  },
};
