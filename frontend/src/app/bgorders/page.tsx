import {  getDataBg } from './api'
import BgOrders from '@/components/bg-orders/BgOrders'

const BgOrdersPage = async ({
  searchParams,
}: {
  searchParams?: {
    page: number
    limit: number
    name: string;
    client: string;
    status: string;
    created_after: string;
    created_before: string;
    order_type: string


  }
}) => {
  const {
    page = 1,
    limit = 20,
    name = '',
    client = '',
    status = '',
    created_after = '',
    created_before ='',
    order_type = '',
  } = (await searchParams) ?? {}
  const dataBgResponse = await getDataBg({
    page,
    limit,
    name,
    status,
    created_after,
    created_before,
    order_type,
    client
  })
  
  return (
    <BgOrders dataResponse={dataBgResponse}/>
  )
}
export default BgOrdersPage
