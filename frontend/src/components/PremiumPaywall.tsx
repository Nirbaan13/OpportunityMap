"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import { ApiError, PaymentConfig } from "@/types/api";

type RazorpaySuccess = {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

type RazorpayOptions = {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  prefill?: { email?: string };
  handler: (response: RazorpaySuccess) => void;
  theme?: { color?: string };
  modal?: { ondismiss?: () => void };
};

type RazorpayFailure = {
  error?: { description?: string };
};

type RazorpayInstance = {
  open: () => void;
  on: (event: "payment.failed", handler: (response: RazorpayFailure) => void) => void;
};

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => RazorpayInstance;
  }
}

function loadRazorpayScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.reject();
  if (window.Razorpay) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-razorpay="1"]');
    if (existing) {
      if (existing.dataset.state === "error") {
        existing.remove();
        void loadRazorpayScript().then(resolve, reject);
        return;
      }
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject());
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.dataset.razorpay = "1";
    script.onload = () => {
      script.dataset.state = "loaded";
      resolve();
    };
    script.onerror = () => {
      script.dataset.state = "error";
      reject(new Error("Could not load Razorpay"));
    };
    document.body.appendChild(script);
  });
}

type PremiumPaywallProps = {
  title?: string;
  compact?: boolean;
  /** Renew mode: let an already-premium member pay again to extend their year. */
  renew?: boolean;
};

type CheckoutStage =
  | "idle"
  | "creating"
  | "open"
  | "verifying"
  | "recovering"
  | "success"
  | "cancelled"
  | "failed";

const ORDER_STORAGE_PREFIX = "opportunitymap.pendingPayment.";
const sleep = (milliseconds: number) =>
  new Promise<void>((resolve) => setTimeout(resolve, milliseconds));

export function PremiumPaywall({
  title = "Unlock premium",
  compact = false,
  renew = false,
}: PremiumPaywallProps) {
  const { user, token, refreshUser, updateUser } = useAuth();
  const [config, setConfig] = useState<PaymentConfig | null>(null);
  const [configError, setConfigError] = useState(false);
  const [stage, setStage] = useState<CheckoutStage>("idle");
  const [error, setError] = useState<string | null>(null);
  const done = stage === "success";
  const pending = ["creating", "open", "verifying", "recovering"].includes(stage);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.paymentConfig();
        if (!cancelled) {
          setConfig(data);
          setConfigError(false);
        }
      } catch {
        if (!cancelled) {
          setConfig(null);
          setConfigError(true);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const orderStorageKey = user ? `${ORDER_STORAGE_PREFIX}${user.id}` : null;

  const reconcile = useCallback(
    async (orderId: string, attempts = 6): Promise<boolean> => {
      if (!token) return false;
      setStage("recovering");
      for (let attempt = 0; attempt < attempts; attempt += 1) {
        try {
          const result = await api.paymentStatus(token, orderId);
          if (result.status === "paid" && result.is_premium) {
            await refreshUser();
            if (orderStorageKey) localStorage.removeItem(orderStorageKey);
            setStage("success");
            return true;
          }
          if (result.status === "failed" || result.status === "refunded") break;
        } catch (reconcileError) {
          if (reconcileError instanceof ApiError && reconcileError.status === 401) {
            throw reconcileError;
          }
        }
        await sleep(1500);
      }
      return false;
    },
    [orderStorageKey, refreshUser, token],
  );

  useEffect(() => {
    if (!orderStorageKey || !token || (user?.is_premium && !renew)) return;
    const pendingOrder = localStorage.getItem(orderStorageKey);
    if (!pendingOrder) return;
    void reconcile(pendingOrder, 1).then((paid) => {
      if (!paid) setStage("idle");
    });
  }, [orderStorageKey, reconcile, renew, token, user?.is_premium]);

  async function unlock() {
    if (!token) return;
    setStage("creating");
    setError(null);
    try {
      if (config?.dev_unlock_available) {
        const unlockedUser = await api.devUnlockPremium(token);
        updateUser(unlockedUser);
        setStage("success");
        return;
      }

      if (!config?.razorpay_enabled) {
        setError("Payments are not configured yet. Ask the admin to add Razorpay keys.");
        return;
      }

      const order = await api.createPaymentOrder(token);
      if (orderStorageKey) localStorage.setItem(orderStorageKey, order.order_id);
      await loadRazorpayScript();
      if (!window.Razorpay) throw new Error("Razorpay failed to load");

      await new Promise<void>((resolve, reject) => {
        let checkoutFinished = false;
        const rzp = new window.Razorpay!({
          key: order.key_id,
          amount: order.amount_paise,
          currency: order.currency,
          name: order.name,
          description: order.description,
          order_id: order.order_id,
          prefill: { email: order.prefill_email },
          theme: { color: "#0f766e" },
          modal: {
            ondismiss: () => {
              if (checkoutFinished) return;
              checkoutFinished = true;
              if (orderStorageKey) localStorage.removeItem(orderStorageKey);
              setStage("cancelled");
              resolve();
            },
          },
          handler: (response) => {
            if (checkoutFinished) return;
            checkoutFinished = true;
            setStage("verifying");
            void (async () => {
              try {
                const paidUser = await api.verifyPayment(token, response);
                updateUser(paidUser);
                if (orderStorageKey) localStorage.removeItem(orderStorageKey);
                setStage("success");
                resolve();
              } catch (verifyError) {
                const recovered = await reconcile(order.order_id);
                if (recovered) {
                  resolve();
                } else {
                  reject(verifyError);
                }
              }
            })();
          },
        });
        rzp.on("payment.failed", (response) => {
          if (checkoutFinished) return;
          checkoutFinished = true;
          if (orderStorageKey) localStorage.removeItem(orderStorageKey);
          setStage("failed");
          reject(new Error(response.error?.description || "Payment was declined."));
        });
        setStage("open");
        rzp.open();
      });
    } catch (err) {
      setStage("failed");
      setError(
        err instanceof ApiError || err instanceof Error
          ? err.message
          : "Payment failed. Try again.",
      );
    }
  }

  if (!user || !token) {
    return (
      <div className={compact ? "" : "rounded-md border border-line bg-paper/80 p-6"}>
        <p className="font-display text-lg font-semibold text-ink">{title}</p>
        <p className="mt-2 text-sm text-ink-soft">
          Browse opportunities free. Create an account and unlock premium for profile,
          recommendations, and deadline alerts.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            href="/login"
            className="rounded-md bg-ink px-4 py-2.5 text-sm font-semibold text-paper transition hover:bg-ink-soft"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
          >
            Create account
          </Link>
        </div>
      </div>
    );
  }

  if (done) {
    return (
      <p className="text-sm text-accent">
        {renew
          ? "Renewed. Another 365 days were added to your membership."
          : "Premium unlocked. Your account is ready to use."}
      </p>
    );
  }

  if (user.is_premium && !renew) {
    return (
      <p className="text-sm text-accent">Premium unlocked. Your account is ready to use.</p>
    );
  }

  return (
    <div className={compact ? "" : "rounded-md border border-line bg-paper/80 p-6"}>
      <p className="font-display text-lg font-semibold text-ink">{title}</p>
      <p className="mt-2 text-sm text-ink-soft">
        {renew
          ? "Renew early to add another 365 days on top of your current expiry."
          : config?.description ??
            "Yearly membership for profile, recommendations, saved opportunities, and alerts."}
      </p>
      {config ? (
        <p className="mt-3 font-display text-2xl font-bold text-ink">
          ₹{config.price_inr}
          <span className="text-base font-medium text-ink-soft"> / 365 days</span>
        </p>
      ) : null}
      <p className="mt-1 text-xs text-ink-soft">
        One-time annual purchase · no automatic charge
      </p>
      <button
        type="button"
        disabled={pending || !config}
        onClick={() => void unlock()}
        className="mt-4 rounded-md bg-ink px-4 py-2.5 text-sm font-semibold text-paper transition hover:bg-ink-soft disabled:opacity-50"
      >
        {pending
          ? stage === "open"
            ? "Complete payment in Razorpay…"
            : stage === "verifying" || stage === "recovering"
              ? "Confirming payment…"
              : "Preparing checkout…"
          : config?.dev_unlock_available
            ? `Start yearly (test) — ₹${config.price_inr}`
            : config
              ? renew
                ? `Renew for ₹${config.price_inr}`
                : `Pay ₹${config.price_inr}`
              : "Loading price…"}
      </button>
      {stage === "cancelled" ? (
        <p className="mt-3 text-sm text-ink-soft">Checkout cancelled. You were not charged.</p>
      ) : null}
      {configError ? (
        <p className="mt-3 text-sm text-danger">
          Could not load secure payment details. Refresh and try again.
        </p>
      ) : null}
      {error ? <p className="mt-3 text-sm text-danger">{error}</p> : null}
    </div>
  );
}
