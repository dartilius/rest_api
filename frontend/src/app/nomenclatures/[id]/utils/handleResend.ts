import { resendOrders } from "../../api";

export const handleResend = async (
    id: string,
    setAlert: (alert: { type: 'success' | 'error'; message: string } | null) => void,
    setOpen: (open: boolean) => void
) => {
    try {
        const res = await resendOrders(id);
        if (res) {
            setAlert({ type: 'success', message: res.message || 'Заказ успешно переотправлен!' });
        } else {
            setAlert({ type: 'error', message: `Неизвестная ошибка` });
        }
        setOpen(true);
    } catch (error) {
        console.error('Ошибка при переотправке заказов:', error);
        setAlert({ type: 'error', message: 'Не удалось переотправить заказы.' });
        setOpen(true);
    }
};