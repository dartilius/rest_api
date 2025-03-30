import { IPlayListsDetail } from '@/types/playListsTypes'
import { Label } from '../data-display/Label'
import { DateTime } from '../data-display/DateTime'
import { OwnerInfo } from '../data-display/OwnerInfo'
import { PlaylistInfo } from '../data-display/PlaylistInfo'
import { Name } from '../data-display/Name'
import { Description } from '../data-display/Description'

interface PlayListDetailCardProps {
  data: IPlayListsDetail
  className?: string
}

const PlayListDetailCard = ({
  data,
  className = '',
}: PlayListDetailCardProps) => {
  return (
    <div
      className={`bg-gradient-to-r from-cyan-600 to-blue-500 rounded-lg shadow p-4 md:p-6 ${className}`}
    >
      <div className='flex flex-col md:flex-row md:items-center md:justify-between gap-2 md:gap-4 mb-4 md:mb-6'>
        <div className='md:text-center w-full'>
          <Label className='text-sm md:text-base'>Плейлист:</Label>
          <Name
            name={data.name}
            className='text-xl md:text-2xl break-words text-sky-200'
          />
        </div>
      </div>
      <div className='grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6'>
        {/* Левая колонка - файлы плейлиста */}
        <div className='space-y-3 md:space-y-4'>
          <div className='bg-sky-100 backdrop-blur-sm rounded-lg p-3 md:p-4'>
            <PlaylistInfo
              playlist={data.files}
              files_count={data.files_count}
              className='text-base md:text-lg text-sky-700'
            />
          </div>
        </div>

        {/* Правая колонка - метаданные */}
        <div className='space-y-3 md:space-y-4'>
          <div className='bg-sky-100 backdrop-blur-sm rounded-lg p-3 md:p-4'>
            <Label className='text-sm md:text-base'>Дата создания:</Label>
            <DateTime
              date={data.created}
              className='text-base md:text-lg text-zinc-900'
            />
          </div>

          <div className='bg-sky-100 backdrop-blur-sm rounded-lg p-3 md:p-4'>
            <Label className='text-sm md:text-base'>Владелец:</Label>
            <OwnerInfo
              owner={data.owner}
              className='text-base md:text-lg text-zinc-900'
            />
          </div>

          <div className='bg-sky-100 backdrop-blur-sm rounded-lg p-3 md:p-4'>
            <Label className='text-sm md:text-base'>Описание:</Label>
            <Description
              description={data.description}
              className='text-base md:text-lg text-zinc-900'
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default PlayListDetailCard
