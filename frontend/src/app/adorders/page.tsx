import AdOrders from '@/components/ad-orders/AdOrders'
import { getDataAd } from './api'

const AdOrdersPage = async ({
  searchParams,
}: {
  searchParams?: {
    page: number
    limit: number
    name: string
    client: string
    status: string
    created_after: string
    created_before: string
    brc_type: string
  }
}) => {
  const {
    page = 1,
    limit = 20,
    name = '',
    client = '',
    status = '',
    created_after = '',
    created_before = '',
    brc_type = '',
  } = (await searchParams) ?? {}

  const dataAdResponse = await getDataAd({
    page,
    client,
    limit,
    name,
    status,
    created_after,
    created_before,
    brc_type,
  })

  return <AdOrders dataResponse={dataAdResponse}/>
}
export default AdOrdersPage
