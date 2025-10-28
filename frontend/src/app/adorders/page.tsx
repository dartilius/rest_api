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
    since_after: string,
    since_before: string,
    until_after: string,
    until_before: string
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
    since_after = '',
    since_before = '',
    until_after = '',
    until_before = ''
  } = (await searchParams) ?? {}

  const dataAdResponse = await getDataAd({
    page,
    limit,
    name,
    status,
    created_after,
    created_before,
    brc_type,
    client,
    since_after,
    since_before,
    until_after,
    until_before,
  })

  return <AdOrders dataResponse={dataAdResponse}/>
}
export default AdOrdersPage
