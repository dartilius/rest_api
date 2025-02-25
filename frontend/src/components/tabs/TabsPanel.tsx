'use client'

import { useStore } from '@/providers/mobx-provider/MobxProvider'
import { AppBar, Box, Paper, Tab, Tabs } from '@mui/material'
import { observer } from 'mobx-react'
import BgOrders from '../bg-orders/BgOrders'
import AdOrders from '../ad-orders/AdOrders'

const TabsPanel = () => {
  const { ordersStore } = useStore()

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    ordersStore.setActiveTabs(newValue)
  }
  const activeTab = ordersStore.activeTab
  return (
    <Box sx={{ width: '100%', height: '100%' }}>

      <Paper elevation={4} sx={{height: '100%'}}>
        <AppBar position='static' color='transparent'>
          <Tabs
            value={activeTab}
            onChange={handleChange}
            indicatorColor='primary'
            textColor='inherit'
            variant='fullWidth'
            aria-label='full width tabs example'
          >
            <Tab color='secondary' value={0} label='Bg-Orders' />
            <Tab value={1} label='AD-Orders' />
          </Tabs>
        </AppBar>

        {activeTab === 0 && <BgOrders />}

        {activeTab === 1 && <AdOrders />}
      </Paper>
    </Box>
  )
}
export default observer(TabsPanel)
