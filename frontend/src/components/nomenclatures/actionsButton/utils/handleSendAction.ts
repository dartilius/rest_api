import { sendActions } from '@/app/nomenclatures/api'
import { useNotification } from '@/hooks/useNotification'

export const useSendAction = () => {
	const { showNotification } = useNotification()

	const handleSendAction = async (id: string, type: string) => {
		try {
			const res = await sendActions(id, type)
			showNotification(`${res.message}`, 'info')
		} catch (error) {
			console.error('Ошибка при отправке действия:', error)
		}
	}

	return { handleSendAction }
}
