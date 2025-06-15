import { getBgOrderDetail } from '@/app/bgorders/api'
import BgOrderDetailCard from '@/components/bg-orders/BgOrderDetailCard'

interface Props {
	params: {
		id: string
	}
}

const BgOrderDetail = async ({ params }: Props) => {
	// Явное ожидание параметров
	const { id } = await new Promise<{ id: string }>((resolve) => resolve(params))

	try {
		const orderDetail = await getBgOrderDetail(id)
		console.log(orderDetail)

		return (
			<div className='container mx-auto p-1'>
				<h1 className='text-xl md:text-2xl text-center font-bold '>Детали заказа</h1>
				<BgOrderDetailCard
					data={orderDetail}
					className='mb-2'
				/>
			</div>
		)
	} catch (error) {
		console.error('Error loading order details:', error)
		return <div className='container mx-auto p-4 text-red-500'>Error loading order details</div>
	}
}

export default BgOrderDetail
