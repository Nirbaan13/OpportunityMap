"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

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
};

declare global {
  interface Window {
    Razorpay?: new (options: RazorpayOptions) => { open: () => void };
  }
}

function loadRazorpayScript(): Promise<void> {
  if (typeof window === "undefined") return Promise.reject();
  if (window.Razorpay) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-razorpay="1"]');
    if (existing) {
      existing.addEventListener("load", () => resolve());
      existing.addEventListener("error", () => reject());
      return;
    }
    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.dataset.razorpay = "1";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Could not load Razorpay"));
    document.body.appendChild(script);
  });
}

type PremiumPaywallProps = {
  title?: string;
  compact?: boolean;
};

export function PremiumPaywall({
  title = "Unlock premium",
  compact = false,
}: PremiumPaywallProps) {
  const { user, token, refreshUser } = useAuth();
  const [config, setConfig] = useState<PaymentConfig | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await api.paymentConfig();
        if (!cancelled) setConfig(data);
      } catch {
        if (!cancelled) setConfig(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const price = config?.price_inr ?? 299;

  async function unlock() {
    if (!token) return;
    setPending(true);
    setError(null);
    try {
      if (config?.dev_unlock_available) {
        await api.devUnlockPremium(token);
        await refreshUser();
        setDone(true);
        return;
      }

      if (!config?.razorpay_enabled) {
        setError("Payments are not configured yet. Ask the admin to add Razorpay keys.");
        return;
      }

      const order = await api.createPaymentOrder(token);
      await loadRazorpayScript();
      if (!window.Razorpay) throw new Error("Razorpay failed to load");

      await new Promise<void>((resolve, reject) => {
        const rzp = new window.Razorpay!({
          key: order.key_id,
          amount: order.amount_paise,
          currency: order.currency,
          name: order.name,
          description: order.description,
          order_id: order.order_id,
          prefill: { email: order.prefill_email },
          theme: { color: "#0f766e" },
          handler: (response) => {
            void (async () => {
              try {
                await api.verifyPayment(token, response);
                await refreshUser();
                setDone(true);
                resolve();
              } catch (err) {
                reject(err);
              }
            })();
          },
        });
        rzp.open();
        // User may close checkout without paying — clear pending on a short delay
        setTimeout(() => setPending(false), 800);
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Payment failed. Try again.");
    } finally {
      setPending(false);
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

  if (user.is_premium || done) {
    return (
      <p className="text-sm text-accent">Premium unlocked — reload if this page still looks locked.</p>
    );
  }

  return (
    <div className={compact ? "" : "rounded-md border border-line bg-paper/80 p-6"}>
      <p className="font-display text-lg font-semibold text-ink">{title}</p>
      <p className="mt-2 text-sm text-ink-soft">
        {config?.description ??
          `Yearly ₹${price} membership for profile, recommendations, saved opportunities, and alerts.`}
      </p>
      <p className="mt-3 font-display text-2xl font-bold text-ink">₹{price}<span className="text-base font-medium text-ink-soft"> / year</span></p>
      <p className="mt-1 text-xs text-ink-soft">Billed yearly · change price later via server config</p>
      <button
        type="button"
        disabled={pending || !config}
        onClick={() => void unlock()}
        className="mt-4 rounded-md bg-ink px-4 py-2.5 text-sm font-semibold text-paper transition hover:bg-ink-soft disabled:opacity-50"
      >
        {pending
          ? "Working…"
          : config?.dev_unlock_available
            ? `Start yearly (test) — ₹${price}`
            : `Pay ₹${price} / year`}
      </button>
      {error ? <p className="mt-3 text-sm text-danger">{error}</p> : null}
    </div>
  );
}
