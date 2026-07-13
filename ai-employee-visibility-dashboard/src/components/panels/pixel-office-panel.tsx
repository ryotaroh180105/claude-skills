'use client'

/*
 * Pixel Office — a department-floor view of every agent and local
 * Claude Code session. One worker per agent/session, seated in the
 * room that matches what they are doing right now:
 *
 *   DEV ROOM      coding / implementation tasks
 *   RESEARCH LAB  search / research tasks
 *   MEETING ROOM  planning / design tasks (workers face each other)
 *   SNS STUDIO    social media operation
 *   ANALYTICS     analysis / reporting
 *   BREAK AREA    idle, waiting for results, offline (zzz)
 *
 * Deliberately minimal chrome: no zoom/pan, no deck log, no layout
 * editor. The scene is a fixed SVG viewBox that scales with its
 * container, so the view never drifts.
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import { useMissionControl, Agent } from '@/store'

interface TaskRow {
  id: number
  title: string
  status: string
  assigned_to?: string | null
  updated_at?: number
}

interface ActivityRow {
  id: number
  actor: string
  description: string
  created_at: number
}

interface SessionRow {
  id: string
  key: string
  agent: string
  kind: string
  model: string
  active: boolean
  lastActivity?: number
  workingDir?: string | null
}

const TASK_STATUS_LABEL: Record<string, string> = {
  in_progress: '作業中',
  assigned: '着手待ち',
  inbox: '受信箱',
  backlog: 'バックログ',
  awaiting_owner: 'オーナー待ち',
  review: 'レビュー待ち',
  quality_review: '品質レビュー',
  done: '完了',
  failed: '失敗',
}

interface AgentWork {
  label: string
  title: string
  active: boolean
}

/** What an agent is doing right now — or the freshest thing it touched. */
function resolveAgentWork(name: string, tasks: TaskRow[]): AgentWork | null {
  const mine = tasks.filter((t) => t.assigned_to === name)
  if (mine.length === 0) return null
  const inProgress = mine.find((t) => t.status === 'in_progress')
  if (inProgress) return { label: '作業中', title: inProgress.title, active: true }
  const assigned = mine.find((t) => t.status === 'assigned')
  if (assigned) return { label: '次のタスク', title: assigned.title, active: false }
  const latest = [...mine].sort((a, b) => (b.updated_at || 0) - (a.updated_at || 0))[0]
  return { label: `直近 (${TASK_STATUS_LABEL[latest.status] || latest.status})`, title: latest.title, active: false }
}

function relativeTime(ts?: number): string {
  if (!ts) return ''
  const diffMin = Math.floor((Date.now() / 1000 - ts) / 60)
  if (diffMin < 1) return 'たった今'
  if (diffMin < 60) return `${diffMin}分前`
  const h = Math.floor(diffMin / 60)
  if (h < 24) return `${h}時間前`
  return `${Math.floor(h / 24)}日前`
}

/** One local Claude Code session = one worker on the floor. */
function sessionToWorker(row: SessionRow, idx: number, nameCount: Map<string, number>): Agent {
  const baseName = String(row.agent || 'session').trim() || 'session'
  const seen = nameCount.get(baseName) || 0
  nameCount.set(baseName, seen + 1)
  const name = seen === 0 ? baseName : `${baseName}#${seen + 1}`
  const nowSec = Math.floor(Date.now() / 1000)
  return {
    id: -5000 - idx,
    name,
    role: row.kind || 'session',
    status: row.active ? 'busy' : 'idle',
    last_seen: row.lastActivity ? Math.floor(row.lastActivity / 1000) : nowSec,
    last_activity: [row.kind, row.model].filter(Boolean).join(' · ') || undefined,
    created_at: nowSec,
    updated_at: nowSec,
  } as Agent
}

/* ------------------------------------------------------------------ */
/* Department classification                                           */
/* ------------------------------------------------------------------ */

type RoomId = 'coding' | 'research' | 'planning' | 'sns' | 'analysis' | 'break'

const ROOM_PATTERNS: Array<{ id: RoomId; re: RegExp }> = [
  { id: 'sns', re: /sns|投稿|ポスト|ツイート|tweet|x運用|マーケ|marketing|instagram|tiktok|フォロワ/i },
  { id: 'analysis', re: /分析|アナライ|集計|レポート|統計|analy|report|metrics|データ/i },
  { id: 'research', re: /調べ|調査|リサーチ|検索|research|search|survey|トレンド|情報収集|探して|investigate/i },
  { id: 'planning', re: /計画|設計|プラン|検討|要件|会議|ミーティング|戦略|ロードマップ|plan|design|architect|spec|strategy|roadmap/i },
  { id: 'coding', re: /実装|コード|修正|バグ|開発|デバッグ|リファクタ|fix|feat|bug|code|implement|refactor|build|deploy|test|型|lint|typecheck|コミット|pr|プルリク|品質/i },
]

function classifyWorker(agent: Agent, work: AgentWork | null): RoomId {
  if (agent.status === 'offline' || agent.status === 'error') return 'break'
  const activelyWorking = agent.status === 'busy' && (work?.active ?? true)
  if (!activelyWorking && agent.status !== 'busy') return 'break'
  const haystack = [work?.active ? work.title : '', agent.last_activity || '', agent.role || ''].join(' ')
  for (const { id, re } of ROOM_PATTERNS) {
    if (re.test(haystack)) return id
  }
  // Busy but unclassifiable: researchers to the lab, everyone else codes.
  if (/research/i.test(agent.role || '')) return 'research'
  return 'coding'
}

/* ------------------------------------------------------------------ */
/* Palette — warm daytime office, flat pixel-art fills (no gradients) */
/* ------------------------------------------------------------------ */

const P = {
  wall: '#f0e7d8',
  wainscot: '#7fc8c0',
  wainscotShade: '#5da8a0',
  floorA: '#e6d3b3',
  floorB: '#dcc59f',
  window: '#aadcf0',
  windowFrame: '#8a6244',
  cloud: '#ffffff',
  skyline: '#6f9fb8',
  deskTop: '#b0805a',
  deskSide: '#8a6244',
  monitorFrame: '#3a4258',
  monitorOff: '#5a6478',
  monitorOn: '#9ff2c8',
  monitorOnAlt: '#c8f7de',
  chair: '#d96a6a',
  outline: '#2b2b3b',
  bubbleBg: '#fffdf5',
  plantPot: '#c98a2f',
  plantLeaf: '#4f9f5f',
  plantLeafDark: '#3f7f4f',
  sign: '#3a4258',
  signText: '#9ff2c8',
  coffee: '#8a5a3a',
  steam: '#ffffff',
  roomLabel: '#6a5a3a',
} as const

const SKIN_TONES = ['#f2c9a0', '#e3b287', '#c99b72']
const HAIR_COLORS = ['#4a3b8c', '#c94f4f', '#3f7f4f', '#c9862f', '#4f6fc9', '#8c4a7f', '#3a3a4a', '#d9a05a']
const SHIRT_COLORS = ['#5a8fd9', '#d9915a', '#5ab89a', '#b85ab0', '#8a7fd9', '#d9c15a', '#d96a6a', '#4aa8b8']

function hashString(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

/* ------------------------------------------------------------------ */
/* Floor plan — fixed rooms, fixed seats                               */
/* ------------------------------------------------------------------ */

const SCENE_W = 480
const SCENE_H = 320

interface RoomDef {
  id: RoomId
  label: string
  x: number
  y: number
  w: number
  h: number
  tint: string
  seats: Array<{ x: number; y: number }>
  desks: boolean
}

const ROOMS: RoomDef[] = [
  {
    id: 'coding', label: 'DEV ROOM', x: 8, y: 56, w: 224, h: 100, tint: '#b8d4ea',
    seats: [{ x: 40, y: 116 }, { x: 96, y: 116 }, { x: 152, y: 116 }, { x: 208, y: 116 }],
    desks: true,
  },
  {
    id: 'research', label: 'RESEARCH LAB', x: 240, y: 56, w: 112, h: 100, tint: '#c2e0b8',
    seats: [{ x: 272, y: 116 }, { x: 326, y: 116 }],
    desks: true,
  },
  {
    id: 'planning', label: 'MEETING ROOM', x: 360, y: 56, w: 112, h: 100, tint: '#b8dce8',
    seats: [{ x: 392, y: 96 }, { x: 438, y: 96 }, { x: 392, y: 148 }, { x: 438, y: 148 }],
    desks: false,
  },
  {
    id: 'sns', label: 'SNS STUDIO', x: 8, y: 164, w: 144, h: 100, tint: '#e8c2dc',
    seats: [{ x: 48, y: 224 }, { x: 112, y: 224 }],
    desks: true,
  },
  {
    id: 'analysis', label: 'ANALYTICS', x: 160, y: 164, w: 144, h: 100, tint: '#e8dcb8',
    seats: [{ x: 200, y: 224 }, { x: 264, y: 224 }],
    desks: true,
  },
  {
    id: 'break', label: 'BREAK AREA', x: 312, y: 164, w: 160, h: 100, tint: '#c2e4d4',
    seats: [{ x: 352, y: 218 }, { x: 388, y: 218 }, { x: 424, y: 218 }, { x: 456, y: 218 }, { x: 370, y: 248 }, { x: 408, y: 248 }],
    desks: false,
  },
]

/** Standing spots in the bottom corridor for workers who overflow their room. */
const CORRIDOR_SPOTS: Array<{ x: number; y: number }> = [
  { x: 80, y: 296 }, { x: 140, y: 296 }, { x: 200, y: 296 }, { x: 260, y: 296 }, { x: 320, y: 296 }, { x: 380, y: 296 },
]

const statusDotClass: Record<Agent['status'], string> = {
  busy: 'bg-void-amber',
  idle: 'bg-void-mint',
  error: 'bg-void-crimson',
  offline: 'bg-muted-foreground/40',
}

const statusText: Record<Agent['status'], string> = {
  busy: '作業中',
  idle: '待機中',
  error: 'エラー',
  offline: 'オフライン',
}

const ROOM_JA: Record<RoomId, string> = {
  coding: '開発室',
  research: 'リサーチ室',
  planning: '会議室',
  sns: 'SNS室',
  analysis: '分析室',
  break: '休憩室',
}

function truncateTask(title: string, max = 13): string {
  const clean = title.replace(/^\[[^\]]*\]\s*/, '')
  return clean.length > max ? `${clean.slice(0, max)}…` : clean
}

/* ------------------------------------------------------------------ */
/* Pixel worker sprite — plain rects, 2-frame animation                */
/* ------------------------------------------------------------------ */

function PixelWorker({ agent, x, y, frame, task, selected }: {
  agent: Agent
  x: number
  y: number
  frame: number
  task: string | null
  selected: boolean
}) {
  const hash = hashString(agent.name.toLowerCase())
  const skin = SKIN_TONES[(hash >> 5) % SKIN_TONES.length]
  const hair = HAIR_COLORS[hash % HAIR_COLORS.length]
  const shirt = SHIRT_COLORS[(hash >> 3) % SHIRT_COLORS.length]
  const hairStyle = (hash >> 7) % 3
  const busy = agent.status === 'busy'
  const idle = agent.status === 'idle'
  const offline = agent.status === 'offline' || agent.status === 'error'
  const armLift = busy && frame === 1 ? -2 : 0
  const blink = idle && frame === 1

  return (
    <g opacity={offline ? 0.35 : 1} filter={offline ? 'grayscale(1)' : undefined}>
      {/* chair back peeking above the desk */}
      <rect x={x - 9} y={y - 2} width={18} height={5} fill={P.chair} />

      {/* body */}
      <rect x={x - 7} y={y - 12} width={14} height={11} fill={shirt} />
      <rect x={x - 10} y={y - 8 + armLift} width={3} height={6} fill={shirt} />
      <rect x={x + 7} y={y - 8 + armLift} width={3} height={6} fill={shirt} />
      <rect x={x - 10} y={y - 2 + armLift} width={3} height={2} fill={skin} />
      <rect x={x + 7} y={y - 2 + armLift} width={3} height={2} fill={skin} />

      {/* head */}
      <rect x={x - 6} y={y - 24} width={12} height={12} fill={skin} />
      {/* hair — three styles for a more crowded-office feel */}
      <rect x={x - 7} y={y - 26} width={14} height={5} fill={hair} />
      {hairStyle === 0 && (
        <>
          <rect x={x - 7} y={y - 22} width={2} height={5} fill={hair} />
          <rect x={x + 5} y={y - 22} width={2} height={5} fill={hair} />
        </>
      )}
      {hairStyle === 1 && (
        <>
          <rect x={x - 5} y={y - 28} width={3} height={3} fill={hair} />
          <rect x={x + 1} y={y - 29} width={3} height={4} fill={hair} />
        </>
      )}
      {hairStyle === 2 && (
        <>
          <rect x={x - 8} y={y - 22} width={3} height={10} fill={hair} />
          <rect x={x + 5} y={y - 22} width={3} height={10} fill={hair} />
        </>
      )}
      {/* eyes (blink when idle) */}
      <rect x={x - 4} y={y - 19} width={2} height={blink ? 1 : 2} fill={P.outline} />
      <rect x={x + 2} y={y - 19} width={2} height={blink ? 1 : 2} fill={P.outline} />

      {/* coffee cup for idle workers */}
      {idle && (
        <g>
          <rect x={x + 14} y={y - 5} width={5} height={5} fill="#ffffff" />
          <rect x={x + 15} y={y - 4} width={3} height={3} fill={P.coffee} />
          <rect x={x + (frame === 0 ? 15 : 17)} y={y - 9} width={1} height={2} fill={P.steam} opacity={0.8} />
        </g>
      )}

      {/* zzz for offline workers */}
      {offline && (
        <text x={x + 10} y={y - 24} fontSize={8} fontFamily="monospace" fill={P.outline} opacity={frame === 0 ? 0.9 : 0.4}>z z</text>
      )}

      {/* typing sparks */}
      {busy && (
        <g fill={P.outline} opacity={0.6}>
          <rect x={x + (frame === 0 ? -12 : 11)} y={y - 5} width={1} height={1} />
        </g>
      )}

      {/* speech bubble with current task */}
      {busy && task && (
        <g>
          <rect x={x - 52} y={y - 44} width={104} height={14} fill={P.bubbleBg} stroke={P.outline} strokeWidth={1} />
          <rect x={x - 2} y={y - 30} width={4} height={3} fill={P.bubbleBg} stroke={P.outline} strokeWidth={1} />
          <text x={x} y={y - 34} fontSize={8} fontFamily="monospace" fill={P.outline} textAnchor="middle">{truncateTask(task)}</text>
        </g>
      )}

      {/* name plate */}
      <rect x={x - 16} y={y + 15} width={32} height={9} fill={selected ? P.sign : P.bubbleBg} stroke={P.outline} strokeWidth={0.5} />
      <text x={x} y={y + 22} fontSize={7} fontFamily="monospace" fill={selected ? P.signText : P.outline} textAnchor="middle">{agent.name.slice(0, 8)}</text>
    </g>
  )
}

function PixelDesk({ x, y, busy, frame }: { x: number; y: number; busy: boolean; frame: number }) {
  return (
    <g>
      <rect x={x - 26} y={y} width={52} height={5} fill={P.deskTop} />
      <rect x={x - 26} y={y + 5} width={52} height={8} fill={P.deskSide} />
      <rect x={x - 9} y={y - 13} width={18} height={13} fill={P.monitorFrame} />
      <rect x={x - 7} y={y - 11} width={14} height={9} fill={busy ? (frame === 0 ? P.monitorOn : P.monitorOnAlt) : P.monitorOff} />
      {busy && (
        <g fill={P.monitorFrame}>
          <rect x={x - 5} y={y - 9} width={frame === 0 ? 8 : 5} height={1} />
          <rect x={x - 5} y={y - 7} width={frame === 0 ? 4 : 9} height={1} />
          <rect x={x - 5} y={y - 5} width={frame === 0 ? 7 : 3} height={1} />
        </g>
      )}
      <rect x={x - 2} y={y - 1} width={4} height={1} fill={P.monitorFrame} />
    </g>
  )
}

/* ------------------------------------------------------------------ */
/* Static scenery                                                      */
/* ------------------------------------------------------------------ */

function Scenery({ frame }: { frame: number }) {
  const tiles = useMemo(() => {
    const out: Array<{ x: number; y: number; a: boolean }> = []
    for (let ty = 48; ty < SCENE_H; ty += 16) {
      for (let tx = 0; tx < SCENE_W; tx += 16) {
        out.push({ x: tx, y: ty, a: ((tx + ty) / 16) % 2 === 0 })
      }
    }
    return out
  }, [])

  return (
    <g>
      {/* wall */}
      <rect x={0} y={0} width={SCENE_W} height={48} fill={P.wall} />
      <rect x={0} y={40} width={SCENE_W} height={8} fill={P.wainscot} />
      <rect x={0} y={46} width={SCENE_W} height={2} fill={P.wainscotShade} />

      {/* windows with a city skyline */}
      {[20, 108].map((wx) => (
        <g key={wx}>
          <rect x={wx} y={6} width={60} height={30} fill={P.windowFrame} />
          <rect x={wx + 2} y={8} width={56} height={26} fill={P.window} />
          <g fill={P.skyline}>
            <rect x={wx + 5} y={22} width={7} height={12} />
            <rect x={wx + 14} y={16} width={9} height={18} />
            <rect x={wx + 25} y={25} width={6} height={9} />
            <rect x={wx + 33} y={13} width={8} height={21} />
            <rect x={wx + 43} y={20} width={10} height={14} />
          </g>
          <rect x={wx + (frame === 0 ? 8 : 11)} y={11} width={12} height={3} fill={P.cloud} />
          <rect x={wx + 29} y={8} width={2} height={26} fill={P.windowFrame} />
        </g>
      ))}

      {/* company sign */}
      <rect x={196} y={8} width={110} height={24} fill={P.sign} />
      <text x={251} y={20} fontSize={9} fontFamily="monospace" fill={P.signText} textAnchor="middle">AI OFFICE Inc.</text>
      <text x={251} y={29} fontSize={5} fontFamily="monospace" fill="#7fa8a0" textAnchor="middle">HQ 34F</text>

      {/* wall clock */}
      <rect x={330} y={10} width={18} height={18} fill="#fffdf5" stroke={P.outline} strokeWidth={1} />
      <rect x={338} y={13} width={2} height={7} fill={P.outline} />
      <rect x={frame === 0 ? 340 : 334} y={18} width={5} height={2} fill={P.outline} />

      {/* elevator with floor indicator */}
      <rect x={396} y={4} width={70} height={40} fill="#c9c2b4" />
      <rect x={400} y={8} width={28} height={36} fill="#9a938a" />
      <rect x={434} y={8} width={28} height={36} fill="#9a938a" />
      <rect x={428} y={8} width={6} height={36} fill="#6e675f" />
      <rect x={418} y={0} width={26} height={7} fill={P.sign} />
      <text x={431} y={5.5} fontSize={5} fontFamily="monospace" fill={P.signText} textAnchor="middle">{frame === 0 ? '34' : '33'}</text>

      {/* checker floor */}
      {tiles.map((t) => (
        <rect key={`${t.x}-${t.y}`} x={t.x} y={t.y} width={16} height={16} fill={t.a ? P.floorA : P.floorB} />
      ))}

      {/* rooms: tinted floor + border + label chip */}
      {ROOMS.map((room) => (
        <g key={room.id}>
          <rect x={room.x} y={room.y} width={room.w} height={room.h} fill={room.tint} opacity={0.28} />
          <rect x={room.x} y={room.y} width={room.w} height={room.h} fill="none" stroke={room.tint} strokeWidth={2} opacity={0.9} />
          <rect x={room.x + 3} y={room.y + 3} width={room.label.length * 5.4 + 8} height={10} fill={P.sign} opacity={0.9} />
          <text x={room.x + 7} y={room.y + 10.5} fontSize={6} fontFamily="monospace" fill={P.signText}>{room.label}</text>
        </g>
      ))}

      {/* meeting room: shared table + wall screen */}
      <rect x={380} y={112} width={72} height={16} fill={P.deskTop} />
      <rect x={380} y={128} width={72} height={4} fill={P.deskSide} />
      <rect x={382} y={74} width={48} height={12} fill={P.monitorFrame} />
      <rect x={384} y={76} width={44} height={8} fill={frame === 0 ? P.monitorOn : P.monitorOnAlt} />
      <rect x={388} y={78} width={frame === 0 ? 20 : 12} height={1.5} fill={P.monitorFrame} />
      <rect x={388} y={81} width={frame === 0 ? 10 : 24} height={1.5} fill={P.monitorFrame} />

      {/* research lab: bookshelf + whiteboard */}
      <rect x={246} y={70} width={26} height={20} fill={P.deskSide} />
      {[0, 1].map((row) => (
        <g key={row}>
          <rect x={248} y={73 + row * 9} width={5} height={6} fill="#c94f4f" />
          <rect x={254} y={73 + row * 9} width={5} height={6} fill="#4f6fc9" />
          <rect x={260} y={73 + row * 9} width={5} height={6} fill="#4f9f5f" />
          <rect x={266} y={73 + row * 9} width={4} height={6} fill="#d9c15a" />
        </g>
      ))}
      <rect x={300} y={68} width={44} height={24} fill="#fffdf5" stroke={P.outline} strokeWidth={1} />
      <rect x={304} y={73} width={frame === 0 ? 24 : 30} height={2} fill="#4f6fc9" />
      <rect x={304} y={78} width={18} height={2} fill="#c94f4f" />
      <rect x={304} y={83} width={frame === 0 ? 30 : 22} height={2} fill={P.outline} opacity={0.6} />

      {/* sns studio: ring light + phone on tripod */}
      <rect x={126} y={178} width={16} height={16} fill="none" stroke="#ffd97f" strokeWidth={3} opacity={frame === 0 ? 1 : 0.7} />
      <rect x={132} y={194} width={3} height={12} fill={P.outline} />
      <rect x={20} y={182} width={10} height={16} fill={P.monitorFrame} />
      <rect x={22} y={184} width={6} height={10} fill={frame === 0 ? '#e8a7d8' : '#f0c2e4'} />

      {/* analytics: wall chart with animated bars */}
      <rect x={252} y={172} width={44} height={28} fill="#fffdf5" stroke={P.outline} strokeWidth={1} />
      <rect x={256} y={frame === 0 ? 186 : 182} width={6} height={frame === 0 ? 10 : 14} fill="#4f6fc9" />
      <rect x={266} y={184} width={6} height={12} fill="#4f9f5f" />
      <rect x={276} y={frame === 0 ? 180 : 184} width={6} height={frame === 0 ? 16 : 12} fill="#c94f4f" />
      <rect x={286} y={188} width={6} height={8} fill="#d9c15a" />

      {/* break area: vending machine, coffee, water cooler, couch */}
      <rect x={320} y={176} width={22} height={38} fill="#c94f4f" />
      <rect x={323} y={180} width={12} height={22} fill={frame === 0 ? '#ffe9a8' : '#ffd97f'} />
      <g fill="#c94f4f">
        <rect x={325} y={183} width={3} height={5} /><rect x={330} y={183} width={3} height={5} />
        <rect x={325} y={191} width={3} height={5} /><rect x={330} y={191} width={3} height={5} />
      </g>
      <rect x={348} y={184} width={16} height={28} fill="#5a5248" />
      <rect x={351} y={188} width={10} height={7} fill={frame === 0 ? P.monitorOn : '#7fd8b0'} />
      <rect x={353} y={200} width={6} height={5} fill="#ffffff" />
      <rect x={frame === 0 ? 355 : 356} y={196} width={1} height={3} fill={P.steam} opacity={0.9} />
      <rect x={444} y={176} width={12} height={26} fill="#e8e4da" />
      <rect x={445} y={168} width={10} height={10} fill="#a8d8f0" />
      <rect x={448} y={frame === 0 ? 174 : 170} width={2} height={2} fill="#ffffff" opacity={0.9} />
      {/* couch behind the seated row */}
      <rect x={340} y={206} width={128} height={8} fill="#4a9a8c" />

      {/* server rack corner (bottom-left, blinking LEDs) */}
      <g>
        <rect x={8} y={278} width={30} height={36} fill="#3a4258" />
        <rect x={11} y={282} width={24} height={7} fill="#2b2f40" />
        <rect x={11} y={292} width={24} height={7} fill="#2b2f40" />
        <rect x={11} y={302} width={24} height={7} fill="#2b2f40" />
        {[0, 1, 2].map((row) => (
          <g key={row}>
            <rect x={13} y={284 + row * 10} width={2} height={2} fill={(frame + row) % 2 === 0 ? '#7fff9f' : '#2f8f4f'} />
            <rect x={17} y={284 + row * 10} width={2} height={2} fill={(frame + row) % 2 === 1 ? '#ffd97f' : '#8f6f2f'} />
          </g>
        ))}
        <text x={23} y={275} fontSize={5} fontFamily="monospace" fill="#8a7a5a" textAnchor="middle">SERVER</text>
      </g>

      {/* plants */}
      {[
        { x: 296, y: 62 }, { x: 156, y: 170 }, { x: 460, y: 284 },
      ].map((p, i) => (
        <g key={i}>
          <rect x={p.x} y={p.y + 12} width={12} height={9} fill={P.plantPot} />
          <rect x={p.x + 2} y={p.y} width={8} height={12} fill={P.plantLeaf} />
          <rect x={p.x - 1} y={p.y + 4} width={5} height={6} fill={P.plantLeafDark} />
          <rect x={p.x + 8} y={p.y + 2} width={5} height={6} fill={P.plantLeafDark} />
        </g>
      ))}
    </g>
  )
}

/* ------------------------------------------------------------------ */
/* Panel                                                               */
/* ------------------------------------------------------------------ */

export function PixelOfficePanel() {
  const { agents: storeAgents } = useMissionControl()
  const [agents, setAgents] = useState<Agent[]>([])
  const [sessionWorkers, setSessionWorkers] = useState<Agent[]>([])
  const [tasks, setTasks] = useState<TaskRow[]>([])
  const [activities, setActivities] = useState<ActivityRow[]>([])
  const [frame, setFrame] = useState(0)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const [agentRes, taskRes, activityRes, sessionRes] = await Promise.all([
        fetch('/api/agents'),
        fetch('/api/tasks?limit=100'),
        fetch('/api/activities?limit=8'),
        fetch('/api/sessions'),
      ])
      if (agentRes.ok) {
        const data = await agentRes.json()
        if (Array.isArray(data.agents)) setAgents(data.agents)
      }
      if (taskRes.ok) {
        const data = await taskRes.json()
        if (Array.isArray(data.tasks)) setTasks(data.tasks)
      }
      if (activityRes.ok) {
        const data = await activityRes.json()
        if (Array.isArray(data.activities)) setActivities(data.activities)
      }
      if (sessionRes.ok) {
        const data = await sessionRes.json().catch(() => ({}))
        const rows = Array.isArray(data?.sessions) ? (data.sessions as SessionRow[]) : []
        const nameCount = new Map<string, number>()
        setSessionWorkers(rows.map((row, idx) => sessionToWorker(row, idx, nameCount)))
      }
    } catch { /* dashboard poll; retry next tick */ }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [fetchData])

  // 2-frame sprite animation; respect prefers-reduced-motion.
  useEffect(() => {
    if (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const interval = setInterval(() => setFrame((f) => (f + 1) % 2), 600)
    return () => clearInterval(interval)
  }, [])

  const allWorkers = useMemo(() => {
    const registered = agents.length > 0 ? agents : storeAgents
    const registeredNames = new Set(registered.map((a) => a.name.toLowerCase()))
    const sessions = sessionWorkers.filter((s) => !registeredNames.has(s.name.toLowerCase()))
    return [
      ...[...registered].sort((a, b) => a.id - b.id),
      ...[...sessions].sort((a, b) => b.id - a.id),
    ]
  }, [agents, storeAgents, sessionWorkers])

  const workByAgent = useMemo(() => {
    const map = new Map<string, AgentWork>()
    for (const agent of allWorkers) {
      const work = resolveAgentWork(agent.name, tasks)
      if (work) map.set(agent.name, work)
    }
    return map
  }, [allWorkers, tasks])

  /** Seat every worker: room by activity, corridor when the room is full. */
  const placedWorkers = useMemo(() => {
    const seatUsage = new Map<RoomId, number>()
    let corridorUsed = 0
    const placed: Array<{ agent: Agent; x: number; y: number; room: RoomId; hasDesk: boolean }> = []
    for (const agent of allWorkers) {
      const roomId = classifyWorker(agent, workByAgent.get(agent.name) || null)
      const room = ROOMS.find((r) => r.id === roomId)!
      const used = seatUsage.get(roomId) || 0
      if (used < room.seats.length) {
        seatUsage.set(roomId, used + 1)
        placed.push({ agent, x: room.seats[used].x, y: room.seats[used].y, room: roomId, hasDesk: room.desks })
      } else if (corridorUsed < CORRIDOR_SPOTS.length) {
        const spot = CORRIDOR_SPOTS[corridorUsed]
        corridorUsed += 1
        placed.push({ agent, x: spot.x, y: spot.y, room: roomId, hasDesk: false })
      }
      // Beyond room + corridor capacity: counted in the header as 席外.
    }
    return placed
  }, [allWorkers, workByAgent])

  const overflowCount = allWorkers.length - placedWorkers.length

  const counts = useMemo(() => {
    const c = { busy: 0, idle: 0, offline: 0 }
    for (const a of allWorkers) {
      if (a.status === 'busy') c.busy += 1
      else if (a.status === 'idle') c.idle += 1
      else c.offline += 1
    }
    return c
  }, [allWorkers])

  const roomById = useMemo(() => {
    const map = new Map<number, RoomId>()
    for (const p of placedWorkers) map.set(p.agent.id, p.room)
    return map
  }, [placedWorkers])

  const selected = allWorkers.find((a) => a.id === selectedId) || null

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-4">
      {/* header */}
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-lg font-semibold text-foreground">Pixel Office</h1>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-void-amber" />作業中 {counts.busy}</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-void-mint" />待機中 {counts.idle}</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-muted-foreground/40" />オフライン {counts.offline}</span>
          {overflowCount > 0 && <span>+{overflowCount} 席外</span>}
        </div>
      </div>

      {/* scene */}
      <div className="rounded-lg border border-border bg-card p-2 md:p-3">
        <svg
          viewBox={`0 0 ${SCENE_W} ${SCENE_H}`}
          className="w-full h-auto rounded"
          style={{ imageRendering: 'pixelated' }}
          role="img"
          aria-label={`オフィス: 作業中${counts.busy}人、待機中${counts.idle}人、オフライン${counts.offline}人`}
        >
          <Scenery frame={frame} />
          {placedWorkers.map(({ agent, x, y, hasDesk }) => (
            <g key={agent.id}>
              <PixelWorker
                agent={agent}
                x={x}
                y={y}
                frame={frame}
                task={workByAgent.get(agent.name)?.title || agent.last_activity || null}
                selected={selectedId === agent.id}
              />
              {hasDesk && <PixelDesk x={x} y={y} busy={agent.status === 'busy'} frame={frame} />}
            </g>
          ))}
          {placedWorkers.length === 0 && (
            <text x={SCENE_W / 2} y={SCENE_H / 2 + 20} fontSize={10} fontFamily="monospace" fill={P.outline} textAnchor="middle">
              エージェント出社待ち…
            </text>
          )}
        </svg>
      </div>

      {/* roster cards (the accessible/clickable layer) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {allWorkers.map((agent) => {
          const work = workByAgent.get(agent.name)
          const room = roomById.get(agent.id)
          const isSelected = selectedId === agent.id
          return (
            <button
              key={agent.id}
              onClick={() => setSelectedId(isSelected ? null : agent.id)}
              aria-pressed={isSelected}
              className={`text-left rounded-md border px-3 py-2 min-h-[44px] transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary ${
                isSelected ? 'border-primary bg-primary/10' : 'border-border bg-card hover:bg-secondary'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full shrink-0 ${statusDotClass[agent.status]}`} />
                <span className="text-sm font-medium text-foreground truncate">{agent.name}</span>
                {room && <span className="text-2xs rounded bg-secondary px-1.5 py-0.5 text-muted-foreground shrink-0">{ROOM_JA[room]}</span>}
                <span className="text-2xs text-muted-foreground ml-auto shrink-0">
                  {statusText[agent.status]}{agent.last_seen ? ` · ${relativeTime(agent.last_seen)}` : ''}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1 truncate">
                {work
                  ? `${work.label}: ${truncateTask(work.title, 30)}`
                  : agent.last_activity || 'タスクなし'}
              </p>
            </button>
          )
        })}
      </div>

      {/* selected detail */}
      {selected && (
        <div className="rounded-md border border-border bg-card px-4 py-3 text-sm">
          <span className="font-medium text-foreground">{selected.name}</span>
          <span className="text-muted-foreground"> — {statusText[selected.status]}</span>
          {selected.role && <span className="text-muted-foreground"> · {selected.role}</span>}
          {roomById.get(selected.id) && <span className="text-muted-foreground"> · {ROOM_JA[roomById.get(selected.id)!]}</span>}
          {workByAgent.get(selected.name) && (
            <p className="text-muted-foreground mt-1">
              {workByAgent.get(selected.name)!.label}: {workByAgent.get(selected.name)!.title}
            </p>
          )}
          {selected.last_activity && (
            <p className="text-muted-foreground mt-1 text-xs">{selected.last_activity}</p>
          )}
        </div>
      )}

      {/* office activity feed — who did what, most recent first */}
      {activities.length > 0 && (
        <div className="rounded-md border border-border bg-card">
          <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-4 pt-3 pb-1">オフィスの動き</h2>
          <ul className="divide-y divide-border">
            {activities.map((a) => (
              <li key={a.id} className="px-4 py-2 flex items-baseline gap-2 text-sm">
                <span className="font-medium text-foreground shrink-0">{a.actor}</span>
                <span className="text-muted-foreground truncate">{a.description}</span>
                <span className="text-2xs text-muted-foreground ml-auto shrink-0">{relativeTime(a.created_at)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
