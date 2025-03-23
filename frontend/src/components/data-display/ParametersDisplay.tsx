import { formatTime } from '@/utils/dateUtils'
import dayjs from 'dayjs'

interface ParametersDisplayProps {
  parameters: {
    daily_start_time: string
    daily_end_time: string
    times_in_hour: number
  }
  className?: string
}

export const ParametersDisplay = ({
  parameters,
  className,
}: ParametersDisplayProps) => {
  return (
    <div className={`grid grid-cols-2 gap-2 ${className}`}>
      <div className='col-span-2'>
        <span className='text-xl text-zinc-900'>Режим работы:</span>
        <div className='flex gap-2'>
          <span>{formatTime(parameters.daily_start_time)}</span>
          <span>-</span>
          <span>{formatTime(parameters.daily_end_time)}</span>
        </div>
      </div>
      <div>
        <span className='text-xl text-zinc-900 text-nowrap'>Трансляций в час:</span>
        <span className='ml-2 font-bold'>{parameters.times_in_hour}</span>
      </div>
    </div>
  )
}
