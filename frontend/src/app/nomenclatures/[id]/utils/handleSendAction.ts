import { sendActions } from "../../api";

export const handleSendAction = async (
    id: string,
    type: string,
    setAlert: (alert: { type: 'success' | 'error'; message: string } | null) => void,
    setOpen: (open: boolean) => void
) => {
    try {
        const res = await sendActions(id, type);
        if (res) {
            setAlert({ type: 'success', message: res.message || 'Действие успешно отправлено!' });
        } else {
            setAlert({ type: 'error', message: `Неизвестная ошибка` });
        }
        setOpen(true);
    } catch (error) {
        console.error('Ошибка при отправке действия:', error);
        setAlert({ type: 'error', message: 'Не удалось отправить действие.' });
        setOpen(true);
    }
};