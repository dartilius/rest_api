import TabsPanel from '@/components/tabs/TabsPanel'
import { getDataAd, getDataBg } from './api'

const OrdersPage = async ({
  searchParams,
}: {
  searchParams?: {
    pageBg: number
    pageAd: number
    limit: number
    name: string
    status: string
    timezone: string
    version: string
  }
}) => {
  const {
    pageBg = 1,
    pageAd = 1,
    limit = 20,
    name = '',
    status = '',
    timezone = '',
    version = '',
  } = (await searchParams) ?? {}
  const dataBgResponse = await getDataBg({
    pageBg,
    limit,
    name,
    status,
    timezone,
    version,
  })
  const dataAdResponse = await getDataAd({
    pageAd,
    limit,
    name,
    status,
    timezone,
    version,
  })
  console.log(dataBgResponse)
  return (
    <TabsPanel
      dataBgResponse={dataBgResponse}
      dataAdResponse={dataAdResponse}
      initialPageBg={pageBg}
      initialPageAd={pageAd}
      initialLimit={limit}
    />
  )
}
export default OrdersPage
