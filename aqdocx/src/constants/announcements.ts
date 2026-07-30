export interface Announcement {
  version: string
  badgeText: string
  title: string
  highlightText: string
  linkText: string
  linkTo: string
}

export const ANNOUNCEMENTS: Record<string, Announcement> = {
  '1.3.9': {
    version: '1.3.9',
    badgeText: 'V1.3.9 Release',
    title: 'Strict auto_migrate=False enforcement, non-fatal DatabaseState readiness model & atomic DDL transactions:',
    highlightText: 'Database Sentinel',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.9',
  },
  '1.3.8': {
    version: '1.3.8',
    badgeText: 'V1.3.8 Release',
    title: 'DSL Migration Generator Overhaul, FK Topological Model Sorting & Scalar Enum Defaults:',
    highlightText: 'Migration Architect',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.8',
  },
  '1.3.7': {
    version: '1.3.7',
    badgeText: 'V1.3.7 Release',
    title: 'Thread-safe ModelRegistry, manager subclass isolation & contract annotations:',
    highlightText: 'Thread Sentinel',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.7',
  },
  '1.3.6': {
    version: '1.3.6',
    badgeText: 'V1.3.6 Release',
    title: 'Unified artifact store (.aquilia/artifacts/), HMAC signatures & CLI:',
    highlightText: 'Artifact Forge',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.6',
  },
  '1.3.5': {
    version: '1.3.5',
    badgeText: 'V1.3.5 Release',
    title: 'Distributed task queues, mail delivery pipeline & zero-dependency HTTP:',
    highlightText: 'Distributed Tide',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.5',
  },
  '1.3.4': {
    version: '1.3.4',
    badgeText: 'V1.3.4 Release',
    title: 'Phase 3 subsystem audit, security & durability fixes:',
    highlightText: 'Structural Integrity',
    linkText: 'Learn More',
    linkTo: '/releases/1.3.4',
  },
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
  return ANNOUNCEMENTS['1.3.9']
}
