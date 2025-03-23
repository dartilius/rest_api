import { IAdOrderDetail } from '@/types/orderTypes'
import StatusBadge from '../data-display/StatusBadge'
import { BroadcastInterval } from '../data-display/BroadcastInterval'
import { ClientInfo } from '../data-display/ClientInfo'
import { DateTime } from '../data-display/DateTime'
import { PlaylistInfo } from '../data-display/PlaylistInfo'
import { Label } from '../data-display/Label'
import { OwnerInfo } from '../data-display/OwnerInfo'
import { ParametersDisplayAd } from '../data-display/ParametersDisplayAd'

interface AdOrderDetailCardProps {
  data: IAdOrderDetail
  className?: string
}

const AdOrderDetailCard = ({
  data,
  className = '',
}: AdOrderDetailCardProps) => {
  return (
    <div
      className={`bg-gradient-to-r from-cyan-600 to-blue-500  rounded-lg shadow p-6 ${className}`}
    >
      {/* Заголовок */}
      <div className='flex flex-col sm:flex-row justify-between items-start gap-4 mb-6'>
        <div>
          <h1 className='text-2xl font-bold'>{data.name}</h1>
          {data.description && (
            <p className='text-gray-600 mt-2'>{data.description}</p>
          )}
        </div>
        <div className='flex flex-col items-end gap-2'>
          <StatusBadge
            status={data.status}
            iconClassName='w-5 h-5'
            className='font-bold'
            size='lg'
          />
        </div>
      </div>

      {/* Основные данные */}
      <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-2xl'>
        <div className='space-y-4'>
          <div>
            <Label>Клиент:</Label>
            <ClientInfo client={data.client} />
          </div>

          <div>
            <Label>Плейлист:</Label>
            <PlaylistInfo playlist={data.playlist} />
          </div>

          <div>
            <Label>Параметры трансляции:</Label>
            <ParametersDisplayAd parameters={data.parameters} />
          </div>
        </div>

        <div className='space-y-4'>
          <div>
            <Label>Период трансляции:</Label>
            <BroadcastInterval interval={data.broadcast_interval} />
          </div>

          <div>
            <Label>Дата создания:</Label>
            <DateTime date={data.created} />
          </div>

          <div>
            <Label>Владелец:</Label>
            <OwnerInfo owner={data.owner} />
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdOrderDetailCard
