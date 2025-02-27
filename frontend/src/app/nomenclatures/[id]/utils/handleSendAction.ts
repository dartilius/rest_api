import {sendActions} from "@/services/NomenclaturesService";

export const handleSendAction = async (
    id: string,
    type: string,
    setAlert: (alert: { type: 'success' | 'error'; message: string } | null) => void,
    setOpen: (open: boolean) => void
) => {
    try {
        const res = await sendActions(id, type);
        if (res.status === 200) {
            setAlert({ type: 'success', message: res.message || 'Действие успешно отправлено!' });
        } else {
            setAlert({ type: 'error', message: `Ошибка: статус ${res.status}, сообщение: ${res.detail}` });
        }
        setOpen(true);
    } catch (error) {
        console.error('Ошибка при отправке действия:', error);
        setAlert({ type: 'error', message: 'Не удалось отправить действие.' });
        setOpen(true);
    }
};