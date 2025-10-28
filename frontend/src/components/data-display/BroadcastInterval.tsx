'use client'
import { DateTime } from './DateTime'

interface BroadcastIntervalProps {
  interval: {
    lower: string
    upper: string
  }
  className?: string
}

export const BroadcastInterval = ({ interval, className }: BroadcastIntervalProps) => {
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <div className="flex items-center gap-2">
        <span className="text-xl text-zinc-700">С:</span>
        <DateTime date={interval.lower} />
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xl text-zinc-700">По:</span>
        <DateTime date={interval.upper} />
      </div>
    </div>
  )
}