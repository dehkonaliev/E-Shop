const priceFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
})

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

const dateTimeFormatter = new Intl.DateTimeFormat('en-US', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

export function formatPrice(value: string | number): string {
  const amount = typeof value === 'string' ? Number.parseFloat(value) : value
  if (Number.isNaN(amount)) return '$0.00'
  return priceFormatter.format(amount)
}

export function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return dateFormatter.format(date)
}

export function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return dateTimeFormatter.format(date)
}

export function initials(value: string): string {
  const parts = value.trim().split(/\s+/).slice(0, 2)
  if (parts.length === 0 || parts[0] === '') return 'E'
  return parts.map((part) => part[0]?.toUpperCase() ?? '').join('')
}

export function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return count === 1 ? singular : plural
}
