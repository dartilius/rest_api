import {resendOrders} from "@/services/NomenclaturesService";

export const handleResend = async (
    id: string,
    setAlert: (alert: { type: 'success' | 'error'; message: string } | null) => void,
    setOpen: (open: boolean) => void
) => {
    try {
        const res = await resendOrders(id);
        if (res.status === 200 || res.status === 201) {
            setAlert({ type: 'success', message: res.message || 'Заказ успешно переотправлен!' });
        } else {
            setAlert({ type: 'error', message: `Ошибка: статус ${res.status}, сообщение: ${res.detail}` });
        }
        setOpen(true);
    } catch (error) {
        console.error('Ошибка при переотправке заказов:', error);
        setAlert({ type: 'error', message: 'Не удалось переотправить заказы.' });
        setOpen(true);
    }
};