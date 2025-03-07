'use client'

import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { AppBar, Box, Paper, Tab, Tabs } from '@mui/material'
import { observer } from 'mobx-react'
import BgOrders from '../bg-orders/BgOrders'
import AdOrders from '../ad-orders/AdOrders'
import FiltersPanel from '../filters/FiltersPanel'

const TabsPanel = ({dataBg}: any) => {
  const data = dataBg
  const { ordersStore } = useStore()
  ordersStore.setDataBg(data)

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    ordersStore.setActiveTabs(newValue)
  }

  const activeTab = ordersStore.activeTab

  return (
    <Paper
      elevation={4}
      sx={{ width: '100%', height: '100%' }}
      className='relative overflow-hidden'
    >
      <AppBar position='static' color='transparent'>
        <Box
          display={'flex'}
          justifyContent={'center'}
          width={'100%'}
          padding={1}
          gap={2}
        >
          <Box
            sx={{ width: 1 / 3 }}
            display={'flex'}
            justifyContent={'center'}
            alignItems={'center'}
          >
            <Tabs
              sx={{
                width: '100%',
                background: 'rgba(255, 255, 255, 0.8)',
                borderRadius: 2,
              }}
              value={activeTab}
              onChange={handleChange}
              indicatorColor='primary'
              textColor='inherit'
              variant='fullWidth'
              aria-label='full width tabs example'
              selectionFollowsFocus
            >
              <Tab
                sx={{
                  borderRadius: '2px',
                }}
                value={0}
                label='Bg-Orders'
              />
              <Tab
                sx={{
                  borderRadius: '2px',
                }}
                value={1}
                label='AD-Orders'
              />
            </Tabs>
          </Box>
          <Box sx={{ width: 2 / 3 }}>
            <FiltersPanel />
          </Box>
        </Box>
      </AppBar>

      {activeTab === 0 && <BgOrders />}
      {activeTab === 1 && <AdOrders />}
    </Paper>
  )
}

export default observer(TabsPanel)
