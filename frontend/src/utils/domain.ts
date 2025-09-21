// Utility to extract domain name without TLD from current hostname
export function getDomainNameFromHost(hostname: string): string {
  // Handle localhost and development
  if (
    hostname === 'localhost' ||
    hostname === '127.0.0.1' ||
    hostname.includes('localhost')
  ) {
    return 'bulletdrop'
  }

  const parts = hostname.split('.')
  if (parts.length >= 2) {
    const commonTlds = [
      'com',
      'page',
      'me',
      'io',
      'org',
      'net',
      'co',
      'dev',
      'app',
      'tech',
      'xyz',
      'club',
    ]
    const lastPart = parts[parts.length - 1].toLowerCase()
    if (commonTlds.includes(lastPart)) {
      return parts[parts.length - 2]
    }
  }
  return parts[0] || hostname
}

export function getCurrentDomainName(): string {
  const hostname = typeof window !== 'undefined' ? window.location.hostname : ''
  return getDomainNameFromHost(hostname)
}
