'use client'

/*
 * Pixel Office — one agent = one pixel-art worker at a desk.
 *
 * Deliberately minimal: no zoom/pan, no deck log, no layout editor.
 * The scene is a fixed SVG viewBox that scales with its container, so the
 * view never drifts. Liveliness comes from the workers themselves:
 * busy = typing + glowing monitor + task speech bubble, idle = coffee,
 * offline = dimmed seat with zzz.
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

/** What an agent is doing right now — or the freshest thing it touched. */
function resolveAgentWork(name: string, tasks: TaskRow[]): { label: string; title: string; active: boolean } | null {
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
  deskTop: '#b0805a',
  deskSide: '#8a6244',
  monitorFrame: '#3a4258',
  monitorOff: '#5a6478',
  monitorOn: '#9ff2c8',
  monitorOnAlt: '#c8f7de',
  chair: '#d96a6a',
  skin: '#f2c9a0',
  outline: '#2b2b3b',
  bubbleBg: '#fffdf5',
  plantPot: '#c98a2f',
  plantLeaf: '#4f9f5f',
  plantLeafDark: '#3f7f4f',
  rug: '#e8a7a7',
  rugEdge: '#d98a8a',
  sign: '#3a4258',
  signText: '#9ff2c8',
  coffee: '#8a5a3a',
  steam: '#ffffff',
} as const

const HAIR_COLORS = ['#4a3b8c', '#c94f4f', '#3f7f4f', '#c9862f', '#4f6fc9', '#8c4a7f']
const SHIRT_COLORS = ['#5a8fd9', '#d9915a', '#5ab89a', '#b85ab0', '#8a7fd9', '#d9c15a']

function hashString(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

/* ------------------------------------------------------------------ */
/* Scene layout — 8 fixed desks in two rows                            */
/* ------------------------------------------------------------------ */

const SCENE_W = 340
const SCENE_H = 210
const DESK_SLOTS: Array<{ x: number; y: number }> = [
  { x: 48, y: 84 }, { x: 122, y: 84 }, { x: 196, y: 84 }, { x: 270, y: 84 },
  { x: 48, y: 152 }, { x: 122, y: 152 }, { x: 196, y: 152 }, { x: 270, y: 152 },
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

function truncateTask(title: string, max = 13): string {
  const clean = title.replace(/^\[[^\]]*\]\s*/, '')
  return clean.length > max ? `${clean.slice(0, max)}…` : clean
}

/* ------------------------------------------------------------------ */
/* Pixel worker sprite — drawn with plain rects, 2-frame animation     */
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
  const hair = HAIR_COLORS[hash % HAIR_COLORS.length]
  const shirt = SHIRT_COLORS[(hash >> 3) % SHIRT_COLORS.length]
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
      {/* arms (rise while typing) */}
      <rect x={x - 10} y={y - 8 + armLift} width={3} height={6} fill={shirt} />
      <rect x={x + 7} y={y - 8 + armLift} width={3} height={6} fill={shirt} />
      {/* hands on keyboard */}
      <rect x={x - 10} y={y - 2 + armLift} width={3} height={2} fill={P.skin} />
      <rect x={x + 7} y={y - 2 + armLift} width={3} height={2} fill={P.skin} />

      {/* head */}
      <rect x={x - 6} y={y - 24} width={12} height={12} fill={P.skin} />
      {/* hair */}
      <rect x={x - 7} y={y - 26} width={14} height={5} fill={hair} />
      <rect x={x - 7} y={y - 22} width={2} height={5} fill={hair} />
      <rect x={x + 5} y={y - 22} width={2} height={5} fill={hair} />
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
      {/* desk top + front */}
      <rect x={x - 26} y={y} width={52} height={5} fill={P.deskTop} />
      <rect x={x - 26} y={y + 5} width={52} height={8} fill={P.deskSide} />
      {/* monitor on desk, facing the viewer (worker sits behind) */}
      <rect x={x - 9} y={y - 13} width={18} height={13} fill={P.monitorFrame} />
      <rect x={x - 7} y={y - 11} width={14} height={9} fill={busy ? (frame === 0 ? P.monitorOn : P.monitorOnAlt) : P.monitorOff} />
      {/* fake code lines while busy */}
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

      {/* windows with sky + drifting cloud */}
      {[30, 250].map((wx) => (
        <g key={wx}>
          <rect x={wx} y={8} width={44} height={26} fill={P.windowFrame} />
          <rect x={wx + 2} y={10} width={40} height={22} fill={P.window} />
          <rect x={wx + 21} y={10} width={2} height={22} fill={P.windowFrame} />
          <rect x={wx + (frame === 0 ? 6 : 8)} y={14} width={10} height={3} fill={P.cloud} />
          <rect x={wx + (frame === 0 ? 26 : 27)} y={22} width={8} height={3} fill={P.cloud} />
        </g>
      ))}

      {/* office sign */}
      <rect x={128} y={10} width={84} height={20} fill={P.sign} />
      <text x={170} y={24} fontSize={10} fontFamily="monospace" fill={P.signText} textAnchor="middle">AI OFFICE</text>

      {/* checker floor */}
      {tiles.map((t) => (
        <rect key={`${t.x}-${t.y}`} x={t.x} y={t.y} width={16} height={16} fill={t.a ? P.floorA : P.floorB} />
      ))}

      {/* rug between desk rows */}
      <rect x={120} y={108} width={100} height={22} fill={P.rug} />
      <rect x={124} y={112} width={92} height={14} fill={P.rugEdge} />

      {/* plants at both ends */}
      {[10, 318].map((px) => (
        <g key={px}>
          <rect x={px} y={182} width={12} height={9} fill={P.plantPot} />
          <rect x={px + 2} y={170} width={8} height={12} fill={P.plantLeaf} />
          <rect x={px - 1} y={174} width={5} height={6} fill={P.plantLeafDark} />
          <rect x={px + 8} y={172} width={5} height={6} fill={P.plantLeafDark} />
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
  const [tasks, setTasks] = useState<TaskRow[]>([])
  const [activities, setActivities] = useState<ActivityRow[]>([])
  const [frame, setFrame] = useState(0)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const fetchData = useCallback(async () => {
    try {
      const [agentRes, taskRes, activityRes] = await Promise.all([
        fetch('/api/agents'),
        fetch('/api/tasks?limit=100'),
        fetch('/api/activities?limit=8'),
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

  const displayAgents = useMemo(() => {
    const source = agents.length > 0 ? agents : storeAgents
    // Stable seating: sort by id so agents keep their desks across polls.
    return [...source].sort((a, b) => a.id - b.id).slice(0, DESK_SLOTS.length)
  }, [agents, storeAgents])

  const workByAgent = useMemo(() => {
    const map = new Map<string, { label: string; title: string; active: boolean }>()
    for (const agent of displayAgents) {
      const work = resolveAgentWork(agent.name, tasks)
      if (work) map.set(agent.name, work)
    }
    return map
  }, [displayAgents, tasks])

  const counts = useMemo(() => {
    const c = { busy: 0, idle: 0, offline: 0 }
    for (const a of displayAgents) {
      if (a.status === 'busy') c.busy += 1
      else if (a.status === 'idle') c.idle += 1
      else c.offline += 1
    }
    return c
  }, [displayAgents])

  const selected = displayAgents.find((a) => a.id === selectedId) || null

  return (
    <div className="p-4 md:p-6 max-w-5xl mx-auto space-y-4">
      {/* header */}
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-lg font-semibold text-foreground">Pixel Office</h1>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-void-amber" />作業中 {counts.busy}</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-void-mint" />待機中 {counts.idle}</span>
          <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-muted-foreground/40" />オフライン {counts.offline}</span>
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
          {displayAgents.map((agent, i) => {
            const slot = DESK_SLOTS[i]
            return (
              <g key={agent.id}>
                <PixelWorker
                  agent={agent}
                  x={slot.x}
                  y={slot.y}
                  frame={frame}
                  task={workByAgent.get(agent.name)?.title || agent.last_activity || null}
                  selected={selectedId === agent.id}
                />
                <PixelDesk x={slot.x} y={slot.y} busy={agent.status === 'busy'} frame={frame} />
              </g>
            )
          })}
          {displayAgents.length === 0 && (
            <text x={SCENE_W / 2} y={SCENE_H / 2 + 20} fontSize={10} fontFamily="monospace" fill={P.outline} textAnchor="middle">
              エージェント出社待ち…
            </text>
          )}
        </svg>
      </div>

      {/* roster cards (the accessible/clickable layer) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {displayAgents.map((agent) => {
          const work = workByAgent.get(agent.name)
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
