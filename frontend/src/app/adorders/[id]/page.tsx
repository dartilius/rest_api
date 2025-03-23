import { getAdOrderDetail } from '@/app/adorders/api'
import AdOrderDetailCard from '@/components/ad-orders/AdOrderDetailCard'

interface Props {
  params: {
    id: string
  }
}

const AdOrderDetail = async ({ params }: Props) => {
  try {
    const orderDetail = await getAdOrderDetail(params.id)
    console.log(orderDetail)

    return (
      <div className='container mx-auto p-4'>
        <h1 className='text-3xl font-bold mb-6'>Детали заказа</h1>
        <AdOrderDetailCard data={orderDetail} className='mb-6' />
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

export default AdOrderDetail
