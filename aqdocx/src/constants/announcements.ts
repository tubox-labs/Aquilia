export interface Announcement {
  version: string
  badgeText: string
  title: string
  highlightText: string
  linkText: string
  linkTo: string
}

export const ANNOUNCEMENTS: Record<string, Announcement> = {
  '1.3.3': {
    version: '1.3.3',
    badgeText: 'V1.3.3 Release',
    title: 'Analytical query capabilities delivered in ORM:',
    highlightText: 'Window Functions & CTEs',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.3',
  },
  '1.3.2': {
    version: '1.3.2',
    badgeText: 'V1.3.2 Release',
    title: 'API Spec compilation & schema inference engine:',
    highlightText: 'Specula Observatory',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.2',
  },
  '1.3.1': {
    version: '1.3.1',
    badgeText: 'V1.3.1 Release',
    title: 'Pluggable identity resolution & unified auth engine:',
    highlightText: 'Auth Backends & DAG Engine',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.1',
  },
  '1.3.0': {
    version: '1.3.0',
    badgeText: 'V1.3.0 Release',
    title: "Aquilia's major validation/molding primitive has been renamed:",
    highlightText: 'Blueprint → Contract',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.0',
  },
}

export function getLatestAnnouncement(version?: string): Announcement {
  if (version && ANNOUNCEMENTS[version]) {
    return ANNOUNCEMENTS[version]
  }
  return ANNOUNCEMENTS['1.3.3']
}
