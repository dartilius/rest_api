import { formatTime } from '@/utils/dateUtils'
import { AdOrderType } from '@/types/orderTypes'
import { Label } from './Label'

interface ParametersDisplayAdProps {
  parameters: {
    end_time?: string | null
    timedelta?: string | null
    start_time?: string | null
    times_in_hour: number
    weight: number
  }
  broadcast_type: AdOrderType
  className?: string
}

export const ParametersDisplayAd = ({
  parameters,
  broadcast_type,
  className,
}: ParametersDisplayAdProps) => {
  const renderSpecificParameters = () => {
    switch (broadcast_type) {
      case AdOrderType.START_OFFSET:
      case AdOrderType.END_OFFSET:
        return parameters.timedelta && (
          <div>
            <Label className='text-2xl'>Смещение по времени:</Label>
            <span className='ml-2 font-bold'>
              {parameters.timedelta.toString()} минут
            </span>
          </div>
        )

      case AdOrderType.SPECIFIC_HOURS:
        return (
          <>
            {parameters.start_time && (
              <div>
                <span className='text-xl text-zinc-900'>Начало:</span>
                <span className='ml-2 font-bold'>
                  {formatTime(parameters.start_time)}
                </span>
              </div>
            )}
            {parameters.end_time && (
              <div>
                <span className='text-xl text-zinc-900'>Окончание:</span>
                <span className='ml-2 font-bold'>
                  {formatTime(parameters.end_time)}
                </span>
              </div>
            )}
          </>
        )

      case AdOrderType.OPEN_TO_HOUR:
        return parameters.end_time && (
          <div>
            <span className='text-xl text-zinc-900'>Окончание:</span>
            <span className='ml-2 font-bold'>
              {formatTime(parameters.end_time)}
            </span>
          </div>
        )

      case AdOrderType.FIXED_TO_CLOSE:
        return parameters.end_time && (
          <div>
            <span className='text-xl text-zinc-900'>Фиксированный час:</span>
            <span className='ml-2 font-bold'>
              {formatTime(parameters.end_time)}
            </span>
          </div>
        )

      case AdOrderType.EVENT_START:
        return parameters.start_time && (
          <div>
            <span className='text-xl text-zinc-900'>Время старта:</span>
            <span className='ml-2 font-bold'>
              {formatTime(parameters.start_time)}
            </span>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className={`grid grid-cols-2 gap-2 ${className}`}>
      {/* Общие параметры для всех типов */}
      <div className='col-span-2'>
        <div>
          <span className='text-xl text-blue-100'>Трансляций в час:</span>
          <span className='ml-2 font-bold'>{parameters.times_in_hour}</span>
        </div>
        <div>
          <span className='text-xl text-blue-100'>Приоритет файла:</span>
          <span className='ml-2 font-bold'>{parameters.weight}</span>
        </div>
      </div>

      {/* Специфические параметры */}
      <div className='col-span-2'>
        {renderSpecificParameters()}
      </div>
    </div>
  )
}