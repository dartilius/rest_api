'use client'
import { IBgOrderDetail } from '@/types/orderTypes'
import StatusBadge from '../data-display/StatusBadge'
import TypeBadge from '../data-display/TypeBadge'
import { BroadcastInterval } from '../data-display/BroadcastInterval'
import { ClientInfo } from '../data-display/ClientInfo'
import { DateTime } from '../data-display/DateTime'
import { ParametersDisplay } from '../data-display/ParametersDisplay'
import { PlaylistInfo } from '../data-display/PlaylistInfo'
import { Label } from '../data-display/Label'
import { OwnerInfo } from '../data-display/OwnerInfo'
import ActionButton from '../Ui/button/ActionButton'
import { Cancel } from '@mui/icons-material'
import { useNotification } from '@/hooks/useNotification'
import { Description } from '../data-display/Description'
import { Name } from '../data-display/Name'

import { useRouter } from 'next/router'
import { cancelBgOrder } from '@/app/bgorders/api'

interface BgOrderDetailCardProps {
  data: IBgOrderDetail
  className?: string
}

const BgOrderDetailCard = ({
  data,
  className = '',
}: BgOrderDetailCardProps) => {
  const { showNotification } = useNotification()
  // const router = useRouter()
  const handleCancelOrder = async () => {
    // setIsCancelling(true);
    try {
      await cancelBgOrder(data.id);
      showNotification('Заказ успешно отменен!', 'success');
      // router.refresh();
    } catch (error) {
      showNotification('Не удалось отменить заказ', 'error');
    } finally {
      // setIsCancelling(false);
    }
  }

  return (
    <div
      className={`bg-gradient-to-r from-cyan-600 to-blue-500  rounded-lg shadow p-6 ${className}`}
    >
      {/* Заголовок */}
      <div className='flex flex-col sm:flex-row justify-between items-start gap-4 '>
        <div>
          <Name name={data.name} />
          {data.description && <Description description={data.description} />}
        </div>
        <div className='flex flex-col items-end gap-2'>
          <TypeBadge
            type={data.order_type}
            className='font-bold'
            iconClassName='w-5 h-5'
            size='lg'
            mode='bg'
          />

          <StatusBadge
            status={data.status}
            iconClassName='w-5 h-5'
            className='font-bold'
            size='lg'
          />
          {data.status === 0 || data.status === 1 ?
          <ActionButton
            variant='warning'
            size='md'
            onClick={handleCancelOrder}
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
            <ParametersDisplay parameters={data.parameters} />
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

export default BgOrderDetailCard
