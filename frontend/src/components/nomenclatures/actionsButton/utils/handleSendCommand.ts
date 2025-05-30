import { sendActions } from '@/app/nomenclatures/api'
import { useNotification } from '@/hooks/useNotification'

export const useSendCommand = () => {
	const { showNotification } = useNotification()

	const handleSendCommand = async (
		id: string,
		type: string,
		parameters: string,
		handleCloseModal: () => void,
		setCommand: (command: string) => void,
	) => {
		try {
			const res = await sendActions(id, type, parameters)
			if (res) {
				handleCloseModal()
				setCommand('')
				showNotification(`${res.message}`, 'info')
			}
		} catch (error) {
			console.error('Ошибка при отправке команды:', error)
			showNotification(`${error}`, 'error')
		}
	}

	return { handleSendCommand }
}
