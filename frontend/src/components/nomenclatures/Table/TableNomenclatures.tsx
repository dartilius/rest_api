'use client'
import CustomPagination from '@/components/Ui/Pagination/CustomPagination'
import { INomenclatures } from '@/types/nomeclaturesType'
import { Box, Theme, useMediaQuery } from '@mui/material'
import { useRef } from 'react'
import DesktopView from './DesctopView'
import MobileView from './MobileView'
import { FiltersWrapper } from '../FiltersWrapper'

type Props = {
  data: INomenclatures[]
  count: any
  limit: number
  page: number
}

export function TableNomenclatures(props: Props) {
  const isMobile = useMediaQuery((theme: Theme) => theme.breakpoints.down('md'))
  const topRef = useRef<HTMLDivElement>(null)
  const { data, count } = props

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <FiltersWrapper />
      
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <Box
          ref={topRef}
          sx={{ height: '1px', width: '100%' }} // Невидимый элемент для скролла
        />
        
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            WebkitOverflowScrolling: 'touch', // Для плавного скролла в iOS
            overscrollBehavior: 'contain', // Предотвращает отскок страницы
            p: 1,
          }}
        >
          {isMobile ? (
            <MobileView data={data} />
          ) : (
            <DesktopView data={data} />
          )}
        </Box>
      </Box>
      
      <Box sx={{ 
        flexShrink: 0,
        p: 0,
        display: 'flex',
        justifyContent: 'center',
        backgroundColor: 'background.paper',
      }}>
        <CustomPagination
          totalItems={count}
          topRef={topRef}
        />
      </Box>
    </Box>
  )
}