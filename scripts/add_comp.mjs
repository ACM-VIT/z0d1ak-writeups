#!/usr/bin/env node

import * as p from '@clack/prompts';
import pc from 'picocolors';
import { existsSync } from 'node:fs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const SCRIPT_FILE = fileURLToPath(import.meta.url);
const SCRIPT_DIR = path.dirname(SCRIPT_FILE);
const REPO_ROOT = path.resolve(SCRIPT_DIR, '..');
const CATEGORIES_FILE = path.join(REPO_ROOT, 'categories.txt');
const GITATTRIBUTES_FILE = path.join(REPO_ROOT, '.gitattributes');
const USER_AGENT = 'Mozilla/5.0 (compatible; z0d1ak-add-comp/2.0)';
const RESET = '\x1b[0m';
const GRAYS = [
  '\x1b[38;5;250m',
  '\x1b[38;5;248m',
  '\x1b[38;5;245m',
  '\x1b[38;5;243m',
  '\x1b[38;5;240m',
  '\x1b[38;5;238m',
  '\x1b[38;5;236m',
];
const BANNER_VARIANTS = [
  {
    name: 'full',
    lines: [
      '░▒▓████████▓▒░▒▓████████▓▒░▒▓███████▓▒░   ░▒▓█▓▒░░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░',
      '       ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓████▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░',
      '     ░▒▓██▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░',
      '   ░▒▓██▓▒░  ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░▒▓████████▓▒░▒▓███████▓▒░',
      ' ░▒▓██▓▒░    ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░',
      '░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░',
      '░▒▓████████▓▒░▒▓████████▓▒░▒▓███████▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░',
    ],
  },
  {
    name: 'medium',
    lines: [
      '███████╗ ██████╗ ██████╗  ██╗ █████╗ ██╗  ██╗',
      '╚══███╔╝██╔═████╗██╔══██╗███║██╔══██╗██║ ██╔╝',
      '  ███╔╝ ██║██╔██║██║  ██║╚██║███████║█████╔╝ ',
      ' ███╔╝  ████╔╝██║██║  ██║ ██║██╔══██║██╔═██╗ ',
      '███████╗╚██████╔╝██████╔╝ ██║██║  ██║██║  ██╗',
      '╚══════╝ ╚═════╝ ╚═════╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝',
    ],
  },
  {
    name: 'compact',
    lines: ['░▒▓ z0d1ak ▓▒░'],
  },
  {
    name: 'tiny',
    lines: ['z0d1ak'],
  },
];

function showHelp() {
  console.log(`
Usage:
  ./add_comp.sh
  ./add_comp.sh <ctftime_event_url>
  ./add_comp.sh --manual

Create a CTF event scaffold using the interactive add comp flow.

Examples:
  ./add_comp.sh
  ./add_comp.sh https://ctftime.org/event/3171/
  ./add_comp.sh --manual
  pnpm run add:comp -- https://ctftime.org/event/3171/
  pnpm run add:comp -- --manual
`);
}

function getTerminalWidth() {
  const envColumns = Number.parseInt(process.env.COLUMNS ?? '', 10);
  if (Number.isFinite(envColumns) && envColumns > 0) {
    return envColumns;
  }

  return process.stdout.columns ?? 80;
}

function getBannerWidth(lines) {
  return Math.max(...lines.map((line) => line.length));
}

function pickBannerVariant(terminalWidth) {
  for (const variant of BANNER_VARIANTS) {
    if (getBannerWidth(variant.lines) <= terminalWidth) {
      return variant;
    }
  }

  return BANNER_VARIANTS[BANNER_VARIANTS.length - 1];
}

function showBanner() {
  const terminalWidth = Math.max(1, getTerminalWidth());
  const variant = pickBannerVariant(terminalWidth);

  console.log();
  for (let index = 0; index < variant.lines.length; index += 1) {
    const line = variant.lines[index] ?? '';
    const color = GRAYS[index] ?? GRAYS[GRAYS.length - 1];
    console.log(`${color}${line}${RESET}`);
  }
  console.log();
}

function exitCancelled(message = 'Setup cancelled') {
  p.cancel(message);
  process.exit(0);
}

function unwrapPrompt(value, message) {
  if (p.isCancel(value)) {
    exitCancelled(message);
  }
  return value;
}

function normalizeUrl(value) {
  return typeof value === 'string' ? value.trim().replace(/\/+$/, '') : '';
}

function parseEventIdFromUrl(input) {
  const trimmed = input.trim();
  if (/^\d+$/.test(trimmed)) {
    return trimmed;
  }

  let parsedUrl;
  try {
    parsedUrl = new URL(trimmed);
  } catch {
    throw new Error('Enter a valid CTFtime event URL.');
  }

  const segments = parsedUrl.pathname.split('/').filter(Boolean);
  const eventIndex = segments.indexOf('event');
  const candidate =
    eventIndex >= 0 && eventIndex + 1 < segments.length
      ? segments[eventIndex + 1]
      : segments[segments.length - 1];

  if (!candidate || !/^\d+$/.test(candidate)) {
    throw new Error(`Could not parse a CTFtime event ID from: ${input}`);
  }

  return candidate;
}

function formatLocation(location) {
  if (!location) {
    return 'N/A';
  }

  if (typeof location === 'string') {
    return location.trim() || 'N/A';
  }

  if (typeof location === 'object') {
    const parts = Object.values(location)
      .flatMap((value) => {
        if (value === null || value === undefined) {
          return [];
        }
        if (typeof value === 'string') {
          return value.trim() ? [value.trim()] : [];
        }
        if (typeof value === 'number' || typeof value === 'boolean') {
          return [String(value)];
        }
        return [];
      })
      .filter(Boolean);

    return parts.length > 0 ? parts.join(', ') : JSON.stringify(location);
  }

  return String(location);
}

function extractDiscordLink(...values) {
  const joined = values.filter(Boolean).join(' ');
  const match = joined.match(/https:\/\/discord\.gg\/[^\s<>"')]+/i);
  return match ? match[0] : '';
}

function normalizeCommaList(value) {
  const seen = new Set();
  const items = [];

  for (const item of value.split(',')) {
    const trimmed = item.trim();
    if (!trimmed || seen.has(trimmed)) {
      continue;
    }
    seen.add(trimmed);
    items.push(trimmed);
  }

  return items;
}

function dedupeList(values) {
  const seen = new Set();
  const items = [];

  for (const value of values) {
    if (!value || seen.has(value)) {
      continue;
    }
    seen.add(value);
    items.push(value);
  }

  return items;
}

function formatList(items, maxItems = 4) {
  if (items.length === 0) {
    return 'none';
  }

  if (items.length <= maxItems) {
    return items.join(', ');
  }

  return `${items.slice(0, maxItems).join(', ')} +${items.length - maxItems} more`;
}

function countLabel(count, noun) {
  return `${count} ${noun}${count === 1 ? '' : 's'}`;
}

function toPosixPath(value) {
  return value.split(path.sep).join('/');
}

function relativeDisplay(targetPath) {
  const relative = path.relative(process.cwd(), targetPath) || '.';
  return relative.startsWith('.') ? relative : `./${relative}`;
}

function escapeGitAttributesPattern(value) {
  return JSON.stringify(toPosixPath(value));
}

function valueOrFallback(value, fallback = 'N/A') {
  if (value === null || value === undefined) {
    return fallback;
  }

  const stringValue = String(value).trim();
  return stringValue.length > 0 && stringValue !== 'null' ? stringValue : fallback;
}

async function ensureEventDirectoryUsesLfs(eventTitle) {
  const patternLine = `${escapeGitAttributesPattern(`${eventTitle}/**`)} filter=lfs diff=lfs merge=lfs -text`;
  const markerLine = '# Keep prose and source files in normal Git.';

  let current = '';
  if (existsSync(GITATTRIBUTES_FILE)) {
    current = await readFile(GITATTRIBUTES_FILE, 'utf8');
  }

  const lines = current.length > 0 ? current.replace(/\r\n/g, '\n').split('\n') : [];
  if (lines.includes(patternLine)) {
    return false;
  }

  const markerIndex = lines.findIndex((line) => line === markerLine);
  if (markerIndex >= 0) {
    lines.splice(markerIndex, 0, patternLine);
  } else {
    if (lines.length > 0 && lines[lines.length - 1] !== '') {
      lines.push('');
    }
    lines.push(patternLine);
  }

  while (lines.length > 1 && lines[lines.length - 1] === '' && lines[lines.length - 2] === '') {
    lines.pop();
  }

  await writeFile(GITATTRIBUTES_FILE, `${lines.join('\n')}\n`, 'utf8');
  return true;
}

function isMetaCtfTag(tag) {
  switch (tag.toLowerCase()) {
    case '100':
    case '101':
    case 'beginner':
    case 'beginners':
    case 'easy':
    case 'expert':
    case 'hard':
    case 'intro':
    case 'introductory':
    case 'junior':
    case 'medium':
    case 'onsite':
    case 'online':
    case 'qual':
    case 'quals':
    case 'remote':
    case 'starter':
    case 'warm-up':
    case 'warmup':
      return true;
    default:
      return false;
  }
}

function looksLikeCtfCategory(tag) {
  return /^(ai|binary.*|blockchain|cloud|crypto|cryptography|forensics|hardware|iot|misc|miscellaneous|mobile|net|network|networking|osint|ppc|programmering|programming|pwn|pwning|re|rev|reverse.*|stego|steganography|terminal|web.*)$/i.test(
    tag
  );
}

function pickCtfdCategory(explicitCategory, tags) {
  if (explicitCategory) {
    return explicitCategory;
  }

  for (const tag of tags) {
    if (tag && looksLikeCtfCategory(tag)) {
      return tag;
    }
  }

  for (const tag of tags) {
    if (tag && !isMetaCtfTag(tag)) {
      return tag;
    }
  }

  for (const tag of tags) {
    if (tag) {
      return tag;
    }
  }

  return 'uncategorized';
}

function asStringArray(values) {
  if (!Array.isArray(values)) {
    return [];
  }

  return values
    .map((item) => {
      if (typeof item === 'string') {
        return item.trim();
      }

      if (item && typeof item === 'object' && typeof item.value === 'string') {
        return item.value.trim();
      }

      return '';
    })
    .filter(Boolean);
}

function buildEventReadme(event, config) {
  const lines = [
    `# ${event.title}`,
    '',
    '| Field        | Value |',
    '|--------------|-------|',
    `| CTFtime      | ${valueOrFallback(event.ctftimeUrl)} |`,
    `| Website      | ${valueOrFallback(event.website)} |`,
    `| Format       | ${valueOrFallback(event.format)} |`,
    `| Restrictions | ${valueOrFallback(event.restrictions)} |`,
    `| Onsite       | ${valueOrFallback(event.onsite)} |`,
    `| Location     | ${valueOrFallback(formatLocation(event.location))} |`,
    `| Weight       | ${valueOrFallback(event.weight)} |`,
    `| Start        | ${valueOrFallback(event.start)} |`,
    `| End          | ${valueOrFallback(event.finish)} |`,
    `| Participants | ${valueOrFallback(event.participants)} |`,
  ];

  if (event.discordLink) {
    lines.push(`| Discord      | ${event.discordLink} |`);
  }

  if (event.liveFeed && event.liveFeed !== 'null') {
    lines.push(`| Live Feed    | ${event.liveFeed} |`);
  }

  lines.push(`| CTFd         | ${config.usesCtfd ? 'yes' : 'no'} |`);
  lines.push('');
  lines.push('## Description');
  lines.push('');
  lines.push(valueOrFallback(event.description, ''));
  lines.push('');

  return `${lines.join('\n')}\n`;
}

function buildChallengeReadme(challenge) {
  const lines = [
    `# ${challenge.name}`,
    '',
    '| Field      | Value |',
    '|------------|-------|',
    `| Category   | ${challenge.category} |`,
    `| Points     | ${valueOrFallback(challenge.value)} |`,
    `| Solves     | ${valueOrFallback(challenge.solves)} |`,
  ];

  if (challenge.tags.length > 0) {
    lines.push(`| Tags       | ${challenge.tags.join(', ')} |`);
  }

  if (challenge.connectionInfo) {
    lines.push(`| Connection | ${challenge.connectionInfo} |`);
  }

  lines.push('');
  lines.push('## Description');
  lines.push('');
  lines.push(valueOrFallback(challenge.description, ''));
  lines.push('');

  if (challenge.files.length > 0) {
    lines.push('## Files');
    lines.push('');
    for (const file of challenge.files) {
      lines.push(`- [${file.name}](./${file.name})`);
    }
    lines.push('');
  }

  lines.push('## Writeup');
  lines.push('');
  lines.push('### Flag');
  lines.push('');
  lines.push('```');
  lines.push('');
  lines.push('```');
  lines.push('');
  lines.push('### Executive Summary');
  lines.push('');
  lines.push('');
  lines.push('### Vulnerability Analysis');
  lines.push('');
  lines.push('');
  lines.push('### Exploit Strategy');
  lines.push('');
  lines.push('');
  lines.push('### Implementation');
  lines.push('');
  lines.push('');
  lines.push('### Execution & Results');
  lines.push('');
  lines.push('');

  return `${lines.join('\n')}\n`;
}

async function loadDefaultCategories() {
  try {
    const raw = await readFile(CATEGORIES_FILE, 'utf8');
    return raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
  } catch {
    return [];
  }
}

async function fetchEventMetadata(eventUrl) {
  const normalizedUrl = normalizeUrl(eventUrl);
  const eventId = parseEventIdFromUrl(normalizedUrl);
  const apiUrl = `https://ctftime.org/api/v1/events/${eventId}/`;

  const response = await fetch(apiUrl, {
    headers: {
      'User-Agent': USER_AGENT,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch event data from ${apiUrl} (HTTP ${response.status})`);
  }

  const data = await response.json();

  return {
    source: 'ctftime',
    eventId,
    title: valueOrFallback(data.title, `Event ${eventId}`),
    ctftimeUrl: normalizedUrl.startsWith('http') ? normalizedUrl : `https://ctftime.org/event/${eventId}`,
    website: typeof data.url === 'string' ? normalizeUrl(data.url) : '',
    start: data.start,
    finish: data.finish,
    format: data.format,
    participants: data.participants,
    description: typeof data.description === 'string' ? data.description : '',
    restrictions: data.restrictions,
    location: data.location,
    weight: data.weight,
    onsite: data.onsite,
    liveFeed: data.live_feed,
    prizes: typeof data.prizes === 'string' ? data.prizes : '',
    discordLink: extractDiscordLink(data.description ?? '', data.prizes ?? ''),
  };
}

async function promptForEventUrl(initialUrl) {
  const value = unwrapPrompt(
    await p.text({
      message: 'CTFtime event URL',
      placeholder: 'https://ctftime.org/event/3171/',
      initialValue: initialUrl,
      validate(input) {
        try {
          parseEventIdFromUrl(input);
          return undefined;
        } catch (error) {
          return error instanceof Error ? error.message : 'Enter a valid CTFtime event URL.';
        }
      },
    }),
    'Setup cancelled'
  );

  return normalizeUrl(value);
}

function validateOptionalUrl(input) {
  const normalized = normalizeUrl(input);
  if (!normalized) {
    return undefined;
  }

  try {
    new URL(normalized);
    return undefined;
  } catch {
    return 'Enter a valid URL or leave blank.';
  }
}

async function promptForOptionalUrl({ message, placeholder, initialValue = '' }) {
  const value = unwrapPrompt(
    await p.text({
      message,
      placeholder,
      initialValue,
      validate: validateOptionalUrl,
    }),
    'Setup cancelled'
  );

  return normalizeUrl(value);
}

async function promptForOptionalText({ message, placeholder, initialValue = '' }) {
  const value = unwrapPrompt(
    await p.text({
      message,
      placeholder,
      initialValue,
    }),
    'Setup cancelled'
  );

  return typeof value === 'string' ? value.trim() : '';
}

async function promptForEventSource() {
  return unwrapPrompt(
    await p.select({
      message: 'How should event metadata be loaded?',
      initialValue: 'ctftime',
      options: [
        {
          value: 'ctftime',
          label: 'Fetch from CTFtime',
          hint: 'Use a CTFtime event URL',
        },
        {
          value: 'manual',
          label: 'Enter manually',
          hint: 'For non-CTFtime or private events',
        },
      ],
    }),
    'Setup cancelled'
  );
}

async function promptForManualEventDetails() {
  const title = unwrapPrompt(
    await p.text({
      message: 'Event title',
      placeholder: 'Internal Security Workshop 2026',
      validate(input) {
        const trimmed = input.trim();
        if (!trimmed) {
          return 'An event title is required.';
        }

        if (trimmed === '.' || trimmed === '..' || /[\\/]/.test(trimmed)) {
          return 'Event title cannot contain path separators.';
        }

        return undefined;
      },
    }),
    'Setup cancelled'
  ).trim();

  const website = await promptForOptionalUrl({
    message: 'Event website',
    placeholder: 'https://example.com',
  });

  const format = await promptForOptionalText({
    message: 'Format',
    placeholder: 'Jeopardy, Attack-Defense, Workshop',
  });

  const restrictions = await promptForOptionalText({
    message: 'Restrictions',
    placeholder: 'Open, Students only, Invite only',
  });

  const onsiteSelection = unwrapPrompt(
    await p.select({
      message: 'Onsite requirement',
      initialValue: 'unknown',
      options: [
        {
          value: 'unknown',
          label: 'Unknown / not specified',
        },
        {
          value: 'false',
          label: 'Online / no onsite requirement',
        },
        {
          value: 'true',
          label: 'Onsite or hybrid requirement',
        },
      ],
    }),
    'Setup cancelled'
  );

  const location = await promptForOptionalText({
    message: 'Location',
    placeholder: 'Optional city, campus, or region',
  });

  const start = await promptForOptionalText({
    message: 'Start time',
    placeholder: '2026-04-10T12:00:00+05:30',
  });

  const finish = await promptForOptionalText({
    message: 'End time',
    placeholder: '2026-04-12T12:00:00+05:30',
  });

  const participants = await promptForOptionalText({
    message: 'Participants',
    placeholder: 'Optional participant count',
  });

  const weight = await promptForOptionalText({
    message: 'Weight',
    placeholder: 'Optional event weight',
  });

  const description = await promptForOptionalText({
    message: 'Description',
    placeholder: 'Optional short description',
  });

  const discordLink = await promptForOptionalUrl({
    message: 'Discord invite',
    placeholder: 'https://discord.gg/example',
  });

  const liveFeed = await promptForOptionalUrl({
    message: 'Live feed URL',
    placeholder: 'https://example.com/live',
  });

  return {
    source: 'manual',
    eventId: '',
    title,
    ctftimeUrl: '',
    website,
    start,
    finish,
    format,
    participants,
    description,
    restrictions,
    location,
    weight,
    onsite: onsiteSelection === 'unknown' ? '' : onsiteSelection,
    liveFeed,
    prizes: '',
    discordLink,
  };
}

async function promptForManualCategories() {
  const defaults = await loadDefaultCategories();
  let selectedDefaults = [];

  if (defaults.length > 0) {
    const selected = unwrapPrompt(
      await p.multiselect({
        message: `Select categories to create ${pc.dim('(space to toggle)')}`,
        options: defaults.map((category) => ({
          value: category,
          label: category,
        })),
        initialValues: defaults,
        required: false,
      }),
      'Setup cancelled'
    );

    selectedDefaults = selected;
  } else {
    p.log.warn(`No default categories found at ${relativeDisplay(CATEGORIES_FILE)}.`);
  }

  const extraInput = unwrapPrompt(
    await p.text({
      message: 'Extra categories',
      placeholder: 'Comma-separated, leave blank to skip',
      defaultValue: '',
    }),
    'Setup cancelled'
  );

  return dedupeList([...selectedDefaults, ...normalizeCommaList(extraInput)]);
}

async function promptForCtfdSettings(defaultBaseUrl) {
  const baseUrl = unwrapPrompt(
    await p.text({
      message: 'CTFd base URL',
      placeholder: valueOrFallback(defaultBaseUrl, 'https://example.ctfd.io'),
      initialValue: defaultBaseUrl,
      validate(input) {
        const normalized = normalizeUrl(input);
        if (!normalized) {
          return 'A CTFd base URL is required.';
        }

        try {
          new URL(normalized);
          return undefined;
        } catch {
          return 'Enter a valid base URL.';
        }
      },
    }),
    'Setup cancelled'
  );

  const token = unwrapPrompt(
    await p.password({
      message: 'Player API token',
      mask: '•',
    }),
    'Setup cancelled'
  );

  return {
    baseUrl: normalizeUrl(baseUrl),
    token: token.trim(),
  };
}

async function probeCtfd(baseUrl, token) {
  let response;
  try {
    response = await fetch(`${baseUrl}/api/v1/challenges`, {
      headers: {
        Authorization: `Token ${token}`,
        'Content-Type': 'application/json',
        'User-Agent': USER_AGENT,
      },
    });
  } catch {
    return {
      ok: false,
      reason: 'Could not reach the CTFd challenge API.',
      challengeIds: [],
      categories: [],
      tags: [],
    };
  }

  if (response.status === 403) {
    return {
      ok: false,
      reason: 'Challenges are not visible to participants yet.',
      challengeIds: [],
      categories: [],
      tags: [],
    };
  }

  if (!response.ok) {
    return {
      ok: false,
      reason: `Could not fetch the challenge list (HTTP ${response.status}).`,
      challengeIds: [],
      categories: [],
      tags: [],
    };
  }

  const payload = await response.json();
  if (!payload.success || !Array.isArray(payload.data)) {
    return {
      ok: false,
      reason: 'CTFd returned an API error while listing challenges.',
      challengeIds: [],
      categories: [],
      tags: [],
    };
  }

  const categories = new Set();
  const tags = new Set();
  const challengeIds = [];

  for (const challenge of payload.data) {
    if (challenge?.id !== null && challenge?.id !== undefined) {
      challengeIds.push(String(challenge.id));
    }

    if (typeof challenge?.category === 'string' && challenge.category.trim()) {
      categories.add(challenge.category.trim());
    }

    for (const tag of asStringArray(challenge?.tags)) {
      tags.add(tag);
    }
  }

  return {
    ok: true,
    challengeIds,
    categories: Array.from(categories),
    tags: Array.from(tags),
  };
}

function fileNameFromUrlish(value) {
  const withoutQuery = value.split('?')[0];

  try {
    const parsed = new URL(withoutQuery, 'https://placeholder.local');
    return path.basename(parsed.pathname);
  } catch {
    return path.basename(withoutQuery);
  }
}

function resolveCtfdFileUrl(filePath, baseUrl) {
  const root = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
  return new URL(filePath, root).toString();
}

async function importCtfdChallenges(eventDir, baseUrl, token, challengeIds, knownCategories) {
  const seededCategories = new Set();
  for (const category of knownCategories) {
    await mkdir(path.join(eventDir, category), { recursive: true });
    seededCategories.add(category);
  }

  const counts = {
    seededCategories: seededCategories.size,
    importedChallenges: 0,
    skippedUnsolved: 0,
    detailFailures: 0,
    downloadedFiles: 0,
    downloadFailures: 0,
  };

  const spinner = p.spinner();
  spinner.start(`Inspecting ${countLabel(challengeIds.length, 'challenge')} from CTFd...`);

  for (const challengeId of challengeIds) {
    spinner.message(`Fetching challenge #${challengeId}...`);

    let payload;
    try {
      const response = await fetch(`${baseUrl}/api/v1/challenges/${challengeId}`, {
        headers: {
          Authorization: `Token ${token}`,
          'Content-Type': 'application/json',
          'User-Agent': USER_AGENT,
        },
      });

      if (!response.ok) {
        counts.detailFailures += 1;
        continue;
      }

      payload = await response.json();
    } catch {
      counts.detailFailures += 1;
      continue;
    }

    if (!payload?.success || !payload.data) {
      counts.detailFailures += 1;
      continue;
    }

    if (payload.data.solved_by_me !== true) {
      counts.skippedUnsolved += 1;
      continue;
    }

    const name = valueOrFallback(payload.data.name, `challenge-${challengeId}`);
    const explicitCategory =
      typeof payload.data.category === 'string' && payload.data.category.trim()
        ? payload.data.category.trim()
        : '';
    const tags = asStringArray(payload.data.tags);
    const effectiveCategory = pickCtfdCategory(explicitCategory, tags);
    const challengeDir = path.join(eventDir, effectiveCategory, name);
    const files = asStringArray(payload.data.files).map((file) => ({
      source: file,
      name: fileNameFromUrlish(file),
    }));

    await mkdir(challengeDir, { recursive: true });
    await writeFile(
      path.join(challengeDir, 'README.md'),
      buildChallengeReadme({
        name,
        category: effectiveCategory,
        value: payload.data.value,
        solves: payload.data.solves,
        tags,
        connectionInfo:
          typeof payload.data.connection_info === 'string' && payload.data.connection_info.trim()
            ? payload.data.connection_info.trim()
            : '',
        description:
          typeof payload.data.description === 'string' ? payload.data.description : '',
        files,
      }),
      'utf8'
    );

    for (const file of files) {
      try {
        const response = await fetch(resolveCtfdFileUrl(file.source, baseUrl), {
          headers: {
            Authorization: `Token ${token}`,
            'User-Agent': USER_AGENT,
          },
        });

        if (!response.ok) {
          counts.downloadFailures += 1;
          continue;
        }

        const bytes = Buffer.from(await response.arrayBuffer());
        await writeFile(path.join(challengeDir, file.name), bytes);
        counts.downloadedFiles += 1;
      } catch {
        counts.downloadFailures += 1;
      }
    }

    counts.importedChallenges += 1;
  }

  spinner.stop(`Imported ${countLabel(counts.importedChallenges, 'solved challenge')}`);
  return counts;
}

function buildEventSummaryLines(event) {
  const lines = [];

  if (event.source === 'manual') {
    lines.push(`  ${pc.dim('Source:')} manual entry`);
  } else {
    lines.push(`  ${pc.dim('CTFtime:')} ${valueOrFallback(event.ctftimeUrl)}`);
  }

  lines.push(`  ${pc.dim('Website:')} ${valueOrFallback(event.website)}`);
  lines.push(
    `  ${pc.dim('Format:')} ${valueOrFallback(event.format)} (${valueOrFallback(event.restrictions)})`
  );
  lines.push(`  ${pc.dim('Start:')} ${valueOrFallback(event.start)}`);
  lines.push(`  ${pc.dim('End:')} ${valueOrFallback(event.finish)}`);

  return lines.join('\n');
}

function buildSetupSummaryLines(eventDir, plan) {
  const lines = [pc.cyan(relativeDisplay(eventDir))];
  lines.push(
    `  ${pc.dim('directory:')} ${existsSync(eventDir) ? 'already exists; files may be updated' : 'new event scaffold'}`
  );
  lines.push('  README.md');

  if (plan.mode === 'manual') {
    lines.push(`  ${pc.dim('flow:')} manual categories`);
    lines.push(`  ${pc.dim('categories:')} ${formatList(plan.categories)}`);
    if (plan.fallbackReason) {
      lines.push(`  ${pc.yellow('fallback:')} ${plan.fallbackReason}`);
    }
  } else {
    lines.push(`  ${pc.dim('flow:')} CTFd solved challenge import`);
    lines.push(`  ${pc.dim('base URL:')} ${plan.baseUrl}`);
    lines.push(`  ${pc.dim('challenge list:')} ${countLabel(plan.challengeIds.length, 'entry')}`);
    if (plan.categories.length > 0) {
      lines.push(`  ${pc.dim('seed categories:')} ${formatList(plan.categories)}`);
    } else if (plan.tags.length > 0) {
      lines.push(`  ${pc.dim('tag fallback:')} ${formatList(plan.tags)}`);
    } else {
      lines.push(`  ${pc.dim('category fallback:')} uncategorized when needed`);
    }
  }

  return lines.join('\n');
}

async function createManualCategories(eventDir, categories) {
  for (const category of categories) {
    await mkdir(path.join(eventDir, category), { recursive: true });
  }

  return {
    createdCategories: categories.length,
  };
}

async function loadCtftimeEvent(initialUrl = '') {
  const eventUrl = initialUrl ? normalizeUrl(initialUrl) : await promptForEventUrl('');
  if (initialUrl) {
    parseEventIdFromUrl(eventUrl);
  }

  const eventSpinner = p.spinner();
  eventSpinner.start('Fetching event metadata...');
  const event = await fetchEventMetadata(eventUrl);
  eventSpinner.stop(`Loaded ${pc.green(event.title)}`);

  return event;
}

async function loadEventDetails(options = {}) {
  const { initialUrl = '', preferManual = false } = options;

  if (initialUrl) {
    return loadCtftimeEvent(initialUrl);
  }

  if (preferManual) {
    return promptForManualEventDetails();
  }

  const source = await promptForEventSource();
  if (source === 'manual') {
    return promptForManualEventDetails();
  }

  return loadCtftimeEvent('');
}

function normalizeRunOptions(options = {}) {
  if (typeof options === 'string') {
    return {
      initialUrl: options,
      preferManual: false,
    };
  }

  return {
    initialUrl: options.initialUrl ?? '',
    preferManual: options.preferManual ?? false,
  };
}

async function runAddComp(options = {}) {
  const { initialUrl, preferManual } = normalizeRunOptions(options);
  showBanner();

  try {
    const event = await loadEventDetails({ initialUrl, preferManual });

    p.note(buildEventSummaryLines(event), event.title);

    const usesCtfd = unwrapPrompt(
      await p.confirm({
        message: 'Does this event use CTFd?',
        initialValue: false,
      }),
      'Setup cancelled'
    );

    let plan;

    if (usesCtfd) {
      const { baseUrl, token } = await promptForCtfdSettings(event.website);

      if (!token) {
        p.log.info('No player token provided. Falling back to manual categories.');
        const categories = await promptForManualCategories();
        plan = {
          mode: 'manual',
          categories,
          fallbackReason: 'No player token provided',
          usesCtfd: true,
        };
      } else {
        const probeSpinner = p.spinner();
        probeSpinner.start('Checking CTFd challenge access...');
        const probe = await probeCtfd(baseUrl, token);

        if (!probe.ok) {
          probeSpinner.stop(pc.yellow('Falling back to manual categories'));
          p.log.warn(probe.reason);
          const categories = await promptForManualCategories();
          plan = {
            mode: 'manual',
            categories,
            fallbackReason: probe.reason,
            usesCtfd: true,
          };
        } else {
          probeSpinner.stop(`Found ${countLabel(probe.challengeIds.length, 'challenge')} in CTFd`);
          plan = {
            mode: 'ctfd',
            baseUrl,
            token,
            challengeIds: probe.challengeIds,
            categories: probe.categories,
            tags: probe.tags,
            usesCtfd: true,
          };
        }
      }
    } else {
      const categories = await promptForManualCategories();
      plan = {
        mode: 'manual',
        categories,
        fallbackReason: '',
        usesCtfd: false,
      };
    }

    const eventDir = path.join(REPO_ROOT, event.title);

    console.log();
    p.note(buildSetupSummaryLines(eventDir, plan), 'Setup Summary');

    const confirmed = unwrapPrompt(
      await p.confirm({
        message: 'Create event scaffold?',
        initialValue: true,
      }),
      'Setup cancelled'
    );

    if (!confirmed) {
      exitCancelled('Setup cancelled');
    }

    const writeSpinner = p.spinner();
    writeSpinner.start('Creating event scaffold...');
    await mkdir(eventDir, { recursive: true });
    const trackedInLfs = await ensureEventDirectoryUsesLfs(event.title);
    await writeFile(
      path.join(eventDir, 'README.md'),
      buildEventReadme(event, { usesCtfd: plan.usesCtfd }),
      'utf8'
    );
    writeSpinner.stop('Event README created');

    let resultLines = [
      pc.cyan(relativeDisplay(eventDir)),
      '  README.md',
    ];

    if (trackedInLfs) {
      resultLines.push(`  ${pc.dim('lfs:')} added ${path.basename(GITATTRIBUTES_FILE)} rule`);
    }

    if (plan.mode === 'manual') {
      const result = await createManualCategories(eventDir, plan.categories);
      resultLines.push(`  ${pc.dim('categories:')} ${countLabel(result.createdCategories, 'folder')}`);
      if (plan.categories.length > 0) {
        resultLines.push(`  ${pc.dim('selected:')} ${formatList(plan.categories)}`);
      }
    } else {
      const result = await importCtfdChallenges(
        eventDir,
        plan.baseUrl,
        plan.token,
        plan.challengeIds,
        plan.categories
      );

      resultLines.push(
        `  ${pc.dim('seed categories:')} ${countLabel(result.seededCategories, 'folder')}`
      );
      resultLines.push(
        `  ${pc.dim('imported:')} ${countLabel(result.importedChallenges, 'solved challenge')}`
      );

      if (result.skippedUnsolved > 0) {
        resultLines.push(
          `  ${pc.dim('unsolved skipped:')} ${countLabel(result.skippedUnsolved, 'challenge')}`
        );
      }

      if (result.downloadedFiles > 0 || result.downloadFailures > 0) {
        resultLines.push(
          `  ${pc.dim('files:')} ${countLabel(result.downloadedFiles, 'download')} / ${countLabel(
            result.downloadFailures,
            'failure'
          )}`
        );
      }

      if (result.detailFailures > 0) {
        resultLines.push(
          `  ${pc.dim('detail fetch failures:')} ${countLabel(result.detailFailures, 'challenge')}`
        );
      }
    }

    console.log();
    p.note(resultLines.join('\n'), 'Scaffold Created');
    console.log();
    p.outro(
      pc.green('Done!') + pc.dim('  Commit the scaffold before adding individual writeups.')
    );
  } catch (error) {
    p.log.error(error instanceof Error ? error.message : 'Unknown error occurred');
    console.log();
    p.outro(pc.red('Setup failed'));
    process.exit(1);
  }
}

const isDirectRun =
  process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url;

if (isDirectRun) {
  const rawArgs = process.argv.slice(2);
  const wantsHelp = rawArgs.includes('--help') || rawArgs.includes('-h');
  const preferManual = rawArgs.includes('--manual');
  const args = rawArgs.filter((arg) => arg !== '--help' && arg !== '-h' && arg !== '--manual');

  if (wantsHelp) {
    showHelp();
    process.exit(0);
  }

  if ((preferManual && args.length > 0) || args.length > 1) {
    console.error('Usage:\n  ./add_comp.sh\n  ./add_comp.sh <ctftime_event_url>\n  ./add_comp.sh --manual');
    process.exit(1);
  }

  await runAddComp({
    initialUrl: args[0] ?? '',
    preferManual,
  });
}

export {
  buildChallengeReadme,
  buildEventReadme,
  fetchEventMetadata,
  loadDefaultCategories,
  normalizeCommaList,
  parseEventIdFromUrl,
  pickCtfdCategory,
  probeCtfd,
  runAddComp,
};
