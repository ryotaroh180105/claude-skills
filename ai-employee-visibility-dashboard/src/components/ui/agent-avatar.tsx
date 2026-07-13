'use client'

import type { ReactElement } from 'react'

interface AgentAvatarProps {
  name?: string | null
  size?: 'xs' | 'sm' | 'md'
  className?: string
}

function hashString(value: string): number {
  let hash = 0
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0
  }
  return hash
}

function getPixelCharacter(name: string, size: 'xs' | 'sm' | 'md'): ReactElement {
  const hash = hashString((name ?? '').toLowerCase())
  const style = hash % 6
  const sizeMap = { xs: 16, sm: 24, md: 32 }
  const s = sizeMap[size]

  const colors = [
    '#00ffff', // cyan
    '#00ff00', // mint
    '#ffff00', // yellow
    '#ff00ff', // magenta
    '#ff6600', // orange
    '#ff0080', // hot pink
  ]
  const color = colors[style]

  const pixelPatterns = [
    // Head
    <>
      <rect x={s * 0.25} y={s * 0.1} width={s * 0.5} height={s * 0.4} fill={color} />
      <rect x={s * 0.1} y={s * 0.4} width={s * 0.8} height={s * 0.5} fill={color} />
      <rect x={s * 0.2} y={s * 0.6} width={s * 0.6} height={s * 0.35} fill={color} />
    </>,
    // Robot style
    <>
      <rect x={s * 0.15} y={s * 0.15} width={s * 0.7} height={s * 0.7} fill={color} />
      <rect x={s * 0.25} y={s * 0.25} width={s * 0.15} height={s * 0.15} fill="currentColor" />
      <rect x={s * 0.6} y={s * 0.25} width={s * 0.15} height={s * 0.15} fill="currentColor" />
    </>,
    // Cute square
    <>
      <rect x={s * 0.2} y={s * 0.1} width={s * 0.6} height={s * 0.6} fill={color} />
      <circle cx={s * 0.35} cy={s * 0.35} r={s * 0.08} fill="currentColor" />
      <circle cx={s * 0.65} cy={s * 0.35} r={s * 0.08} fill="currentColor" />
      <rect x={s * 0.4} y={s * 0.7} width={s * 0.2} height={s * 0.15} fill={color} />
    </>,
    // Triangle
    <>
      <polygon points={`${s * 0.5},${s * 0.1} ${s * 0.1},${s * 0.8} ${s * 0.9},${s * 0.8}`} fill={color} />
      <circle cx={s * 0.5} cy={s * 0.35} r={s * 0.08} fill="currentColor" />
    </>,
    // Star-like
    <>
      <polygon points={`${s * 0.5},${s * 0.1} ${s * 0.6},${s * 0.4} ${s * 0.9},${s * 0.4} ${s * 0.65},${s * 0.65} ${s * 0.75},${s * 0.95} ${s * 0.5},${s * 0.7} ${s * 0.25},${s * 0.95} ${s * 0.35},${s * 0.65} ${s * 0.1},${s * 0.4} ${s * 0.4},${s * 0.4}`} fill={color} />
    </>,
    // Diamond
    <>
      <polygon points={`${s * 0.5},${s * 0.1} ${s * 0.85},${s * 0.5} ${s * 0.5},${s * 0.9} ${s * 0.15},${s * 0.5}`} fill={color} />
      <rect x={s * 0.35} y={s * 0.35} width={s * 0.3} height={s * 0.3} fill="currentColor" />
    </>,
  ]

  return (
    <svg
      width={s}
      height={s}
      viewBox={`0 0 ${s} ${s}`}
      className="shrink-0"
      role="img"
      aria-label={name || 'Agent'}
      style={{ imageRendering: 'pixelated' }}
    >
      <title>{name ?? 'Agent'}</title>
      <rect width={s} height={s} fill="transparent" />
      {pixelPatterns[style]}
    </svg>
  )
}

const sizeClasses: Record<NonNullable<AgentAvatarProps['size']>, string> = {
  xs: 'w-5 h-5',
  sm: 'w-6 h-6',
  md: 'w-8 h-8',
}

export function AgentAvatar({ name, size = 'sm', className = '' }: AgentAvatarProps) {
  return (
    <div className={`${sizeClasses[size]} text-white/70 ${className}`}>
      {getPixelCharacter(name ?? '', size)}
    </div>
  )
}

