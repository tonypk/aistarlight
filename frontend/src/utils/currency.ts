import { useAuthStore } from "@/stores/auth";

const jurisdictionCurrency: Record<
  string,
  { code: string; symbol: string; locale: string }
> = {
  PH: { code: "PHP", symbol: "₱", locale: "en-PH" },
  SG: { code: "SGD", symbol: "S$", locale: "en-SG" },
  LK: { code: "LKR", symbol: "Rs", locale: "en-LK" },
};

function currencyInfo() {
  const auth = useAuthStore();
  return jurisdictionCurrency[auth.jurisdiction] ?? jurisdictionCurrency.PH;
}

export function currencyCode(): string {
  return currencyInfo().code;
}

export function currencySymbol(): string {
  return currencyInfo().symbol;
}

export function currencyLocale(): string {
  return currencyInfo().locale;
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat(currencyLocale(), {
    style: "currency",
    currency: currencyCode(),
  }).format(amount);
}

export function formatAmount(amount: number): string {
  return amount.toLocaleString(currencyLocale(), {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}
