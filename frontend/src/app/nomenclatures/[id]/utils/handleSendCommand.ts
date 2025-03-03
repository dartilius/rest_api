import {sendActions} from "@/services/NomenclaturesService";

export const handleSendCommand = async (
    id: string,
    type: string,
    setAlert: (alert: { type: 'success' | 'error'; message: string } | null) => void,
    setOpen: (open: boolean) => void,
    parameters: string,
    handleCloseModal: () => void,
    setCommand: (command: string) => void,
) => {
    try {
        const res = await sendActions(id, type, parameters);
        if (res.status === 200) {
            setAlert({ type: 'success', message: res.message || 'Команда успешна отправлена!' });
            handleCloseModal()
            setCommand('')
        } else {
            setAlert({ type: 'error', message: `Ошибка: статус ${res.status}, сообщение: ${res.detail}` });
        }
        setOpen(true);
    } catch (error) {
        console.error('Ошибка при отправке команды:', error);
        setAlert({ type: 'error', message: 'Не удалось отправить команду.' });
        setOpen(true);
    }
};