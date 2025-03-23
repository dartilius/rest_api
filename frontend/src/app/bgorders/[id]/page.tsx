import { getBgOrderDetail } from '@/app/bgorders/api'
import BgOrderDetailCard from '@/components/bg-orders/BgOrderDetailCard'

interface Props {
  params: {
    id: string
  }
}

const BgOrderDetail = async ({ params }: Props) => {
  try {
    const orderDetail = await getBgOrderDetail(params.id)
    console.log(orderDetail)

    return (
      <div className='container mx-auto p-4'>
        <h1 className='text-3xl font-bold mb-6'>Детали заказа</h1>
        <BgOrderDetailCard data={orderDetail} className='mb-6' />
      </div>
    )
  } catch (error) {
    console.error('Error loading order details:', error)
    return (
      <div className='container mx-auto p-4 text-red-500'>
        Error loading order details
      </div>
    )
  }
}

export default BgOrderDetail
