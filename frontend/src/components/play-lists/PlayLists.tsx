'use client'
import { useStore } from '@/providers/mobx-provider/MobxProvider'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import { observer } from 'mobx-react'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import AppBar from '@mui/material/AppBar'
import { Typography } from '@mui/material'
import { IDataPlayListsResponse, IPlayList } from '@/types/playListsTypes'

interface IProps {
  dataPlayLists: IDataPlayListsResponse
}
const PlayLists = ({ ...props }: IProps) => {
  const { dataPlayLists } = props

  const { playListsStore } = useStore()
  const [data, setData] = useState<IPlayList[]>([])
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const { totalPages } = playListsStore
  const page = searchParams.get('page')

  const isNextButtonDisabled = Number(page) >= totalPages

  useEffect(() => {
    const params = new URLSearchParams(searchParams)
    if (!params.has('page')) {
      params.set('page', '1')
      router.replace(`${pathname}?${params.toString()}`)
    }

    setData(dataPlayLists.results)
    // Заменяем прямое присваивание на вызов action
    playListsStore.setTotalCount(dataPlayLists.count)
  }, [])

  const handleClick = (id: string) => {
    // Переход на страницу с расшифровкой
    router.push(`playlists/${id}`)
  }

  const goToPage = (newPage: number) => {
    const params = new URLSearchParams(searchParams)
    params.set('page', newPage.toString())
    router.push(`${pathname}?${params.toString()}`)
  }

  return (
    <Paper
      elevation={4}
      sx={{ width: '100%', height: '100%' }}
      className='relative overflow-y-auto'
    >
      <AppBar position='static' color='transparent'>
        <Box
          display={'flex'}
          justifyContent={'center'}
          width={'100%'}
          padding={1}
          gap={2}
        >
          <Typography
            variant='h5'
            noWrap
            component='div'
            fontStyle={'uppercase'}
            sx={{
              flexGrow: 1,
              alignSelf: 'center',
              justifyContent: 'center',
              alignItems: 'center',
              textAlign: 'center',
              fontSize: '2rem',
              fontStyle: 'oblique',
              fontVariantCaps: 'all-small-caps',
              color: '#152c4d',
            }}
          >
            Play lists
          </Typography>
          {/* <Box sx={{ width: 2 / 3 }}>
            <FiltersPanel />
          </Box> */}
        </Box>
      </AppBar>
      <div className='p-2 w-full'>
        <div className='flex flex-col gap-3'>
          {data.map((v) => (
            <div
              className='
        uppercase 
        cursor-pointer 
        border-b-2 
        border-transparent
        
        text-sky-800 
        px-4 
        py-3 
        rounded-lg
        transition-all 
        duration-300 
        hover:bg-sky-50 
        hover:scale-[1.02] 
        hover:shadow-md
        hover:border-sky-200
        active:scale-95
        active:bg-sky-100
        focus:outline-none
        focus:ring-2 
        focus:ring-sky-300
        transform 
        origin-left
        flex
        flex-row
        nowrap
        w-full
      
      '
              onClick={() => handleClick(v.id)}
              key={v.id}
            >
              <span className='w-1/3   font-bold'>{v.name}</span>
              <span className='w-2/3'>создан: {v.created}</span>
            </div>
          ))}
        </div>
        <div className='w-full flex items-center justify-center gap-2 p-4'>
          <button
            onClick={() => goToPage(Number(page) - 1)}
            disabled={Number(page) === 1}
            className='px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300'
          >
            Предыдущая
          </button>
          <span>
            Страница: {Number(page)} из {totalPages}
          </span>
          <button
            onClick={() => goToPage(Number(page) + 1)}
            disabled={isNextButtonDisabled}
            className='px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300'
          >
            Следующая
          </button>
        </div>
      </div>
    </Paper>
  )
}

export default observer(PlayLists)
