import { sendActions } from "../../api";

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
        if (res) {
            setAlert({ type: 'success', message: res.message || 'Команда успешна отправлена!' });
            handleCloseModal()
            setCommand('')
        } else {
            setAlert({ type: 'error', message: `Неизвестная ошибка` });
        }
        setOpen(true);
    } catch (error) {
        console.error('Ошибка при отправке команды:', error);
        setAlert({ type: 'error', message: 'Не удалось отправить команду.' });
        setOpen(true);
    }
};