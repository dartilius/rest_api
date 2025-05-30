import { resendOrders } from '@/app/nomenclatures/api'
import { useNotification } from '@/hooks/useNotification'

export const useResend = () => {
	const { showNotification } = useNotification()

	const handleResend = async (id: string) => {
		try {
			const res = await resendOrders(id)
			showNotification(`${res.message}`, 'info')
		} catch (error) {
			console.error('Ошибка при отправке действия:', error)
		}
	}

	return { handleResend }
}
