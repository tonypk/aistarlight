import { useAuthStore } from '@/stores/auth'

export function currencyCode(): string {
  const auth = useAuthStore()
  return auth.jurisdiction === 'SG' ? 'SGD' : 'PHP'
}

export function currencySymbol(): string {
  const auth = useAuthStore()
  return auth.jurisdiction === 'SG' ? 'S$' : '₱'
}

export function currencyLocale(): string {
  const auth = useAuthStore()
  return auth.jurisdiction === 'SG' ? 'en-SG' : 'en-PH'
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat(currencyLocale(), {
    style: 'currency',
    currency: currencyCode(),
  }).format(amount)
}

export function formatAmount(amount: number): string {
  return amount.toLocaleString(currencyLocale(), {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}
