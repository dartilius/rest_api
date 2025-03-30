'use client'
import { IAdOrderDetail } from '@/types/orderTypes'
import StatusBadge from '../data-display/StatusBadge'
import { BroadcastInterval } from '../data-display/BroadcastInterval'
import { ClientInfo } from '../data-display/ClientInfo'
import { DateTime } from '../data-display/DateTime'
import { PlaylistInfo } from '../data-display/PlaylistInfo'
import { Label } from '../data-display/Label'
import { OwnerInfo } from '../data-display/OwnerInfo'
import { ParametersDisplayAd } from '../data-display/ParametersDisplayAd'
import TypeBadge from '../data-display/TypeBadge'
import { useNotification } from '@/hooks/useNotification'
import { Description } from '../data-display/Description'
import ActionButton from '../Ui/button/ActionButton'
import { Cancel } from '@mui/icons-material'
import { Name } from '../data-display/Name'

interface AdOrderDetailCardProps {
  data: IAdOrderDetail
  className?: string
}

const AdOrderDetailCard = ({
  data,
  className = '',
}: AdOrderDetailCardProps) => {
  const { showNotification } = useNotification()

  const handleButtonCancel = () => {
    showNotification('Заказ отменен!', 'success')
    showNotification('Ошибка отмены заказа', 'error', {
      autoClose: 7000,
      theme: 'dark',
    })
  }
console.log(data.status);

  return (
    <div
      className={`bg-gradient-to-r from-cyan-600 to-blue-500  rounded-lg shadow p-6 ${className}`}
    >
      {/* Заголовок */}
      <div className='flex flex-col sm:flex-row justify-between items-start gap-4'>
        <div>
          <Name name={data.name} />
          {data.description && <Description description={data.description} />}
        </div>
        <div className='flex flex-col items-end gap-2'>
          <TypeBadge
            type={data.broadcast_type}
            className='font-bold'
            iconClassName='w-5 h-5'
            size='lg'
            mode='ad'
          />
          <StatusBadge
            status={data.status}
            iconClassName='w-5 h-5'
            className='font-bold'
            size='lg'
          />
         {/* отображаем кнопку только если статус заказа в эфире или ожидает эфира */}
          {data.status === 0 || data.status === 1 ?
          <ActionButton
            variant='warning'
            size='md'
            onClick={handleButtonCancel}
            icon={Cancel} // Импортировать из MUI или любой другой библиотеки
          >
            Отменить заказ
          </ActionButton> : null}
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
            <PlaylistInfo playlist={[data.playlist]} />
          </div>

          <div>
            <Label>Параметры трансляции:</Label>
            <ParametersDisplayAd
              broadcast_type={data.broadcast_type}
              parameters={data.parameters}
            />
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
