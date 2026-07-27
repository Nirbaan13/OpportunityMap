import Image from "next/image";

type BrandMarkProps = {
  className?: string;
};

export function BrandMark({ className = "h-9 w-9" }: BrandMarkProps) {
  return (
    <Image
      src="/logo.png"
      alt="OpportunityMap"
      width={512}
      height={512}
      priority
      className={`rounded-lg object-cover ${className}`}
    />
  );
}
