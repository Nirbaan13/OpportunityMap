type BrandMarkProps = {
  className?: string;
};

export function BrandMark({ className = "h-7 w-7" }: BrandMarkProps) {
  return (
    <svg
      viewBox="0 0 64 64"
      role="img"
      aria-hidden="true"
      focusable="false"
      className={className}
    >
      <defs>
        <linearGradient id="brandmark-bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#14b8a6" />
          <stop offset="100%" stopColor="#0f766e" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="15" fill="url(#brandmark-bg)" />
      <path
        d="M32 13c-7.4 0-13.4 5.8-13.4 13 0 9.6 11.6 20.9 12.6 21.9a1.2 1.2 0 0 0 1.7 0c1-1 12.6-12.3 12.6-21.9 0-7.2-6-13-13.5-13Z"
        fill="#ffffff"
      />
      <circle cx="32" cy="26" r="5.4" fill="#0f766e" />
    </svg>
  );
}
