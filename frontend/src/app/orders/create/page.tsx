'use client'

import { ChangeEvent, useState } from 'react';
import { Input, ButtonForward, ButtonBack } from '@/src/components/ui';
import {DateRangePicker, RangeValue, Select, SelectItem} from "@nextui-org/react";
import { DateValue, parseDate } from "@internationalized/date";
import {useBgOrderCreateQuery} from "@/src/hooks/orders/useBgOrdersQuery";
import {IBgOrderCreate} from "@/src/types/interface/orders.interface";
import useNomenclaturesQuery from "@/src/hooks/nomenclatures/useNomenclaturesQuery";

function CreateOrders() {
    const { mutate: createBgOrder } = useBgOrderCreateQuery();
    const [inputValues, setInputValues] = useState({
        name: '',
        description: ''
    });
    const [currentStep, setCurrentStep] = useState(1);
    const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
        start: '',
        end: ''
    });
    const [startTime, setStartTime] = useState('09:00:00'); // Время по умолчанию
    const [endTime, setEndTime] = useState('09:00:00');

    const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
        const { name, value } = event.target;
        setInputValues((prevValues) => ({
            ...prevValues,
            [name]: value
        }));
    };

    const { data: nomenclaturesList } = useNomenclaturesQuery({
        page: 1,
        limit: 25
    })

    const handleNextStep = () => {
        if (currentStep < 3) setCurrentStep((prevStep) => prevStep + 1);
    };

    const handlePreviousStep = () => {
        if (currentStep > 1) setCurrentStep((prevStep) => prevStep - 1);
    };

    const formatDateToCustomString = (date: Date, time: string) => {
        const year = date.getFullYear().toString().padStart(4, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day} ${time}`;
    };

    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    const handleDateRangeChange = (range: RangeValue<DateValue>) => {
        const startDate = range.start ? formatDateToCustomString(new Date(range.start.year, range.start.month - 1, range.start.day), startTime) : '';
        const endDate = range.end ? formatDateToCustomString(new Date(range.end.year, range.end.month - 1, range.end.day), endTime) : '';
        setDateRange({ start: startDate, end: endDate });
    };

    const handleStartTimeChange = (event: ChangeEvent<HTMLInputElement>) => {
        const time = event.target.value;
        setStartTime(time);
        if (dateRange.start) {
            const datePart = dateRange.start.split(' ')[0];
            setDateRange((prev) => ({ ...prev, start: `${datePart} ${time}` }));
        }
    };

    const handleEndTimeChange = (event: ChangeEvent<HTMLInputElement>) => {
        const time = event.target.value;
        setEndTime(time);
        if (dateRange.end) {
            const datePart = dateRange.end.split(' ')[0];
            setDateRange((prev) => ({ ...prev, end: `${datePart} ${time}` }));
        }
    };

    const handleSubmit = () => {
        const orderData: IBgOrderCreate = {
            name: inputValues.name,
            broadcast_interval: {
                lower: dateRange.start,
                upper: dateRange.end,
            },
            clients: ['2f1900f5-b345-428b-866f-353927d36d7b', 'e3d74180-30d2-4bc7-b61a-43143c9d5f7f'], // Заполните логикой выбора клиентов
            playlist: 'ec79d8b0-10a2-4107-9354-ac603d56953d', // Здесь должна быть ссылка на выбранный плейлист
            order_type: 1, // Укажите значение order_type
            description: inputValues.description
        };

        // Используйте мутацию для создания заказа
        createBgOrder([orderData]);
    };

    if (!nomenclaturesList) {
        return <></>
    }

    return (
        <div>
            {currentStep === 1 && (
                <div>
                    <div className='center'>
                        <Input
                            required
                            name="name"
                            placeholder="Введите название"
                            label="Название*"
                            onChange={handleInputChange}
                            value={inputValues.name}
                        />
                        <Input
                            required
                            name="description"
                            placeholder="Введите описание"
                            label="Описание"
                            onChange={handleInputChange}
                            value={inputValues.description}
                        />
                    </div>
                    <ButtonForward onClick={handleNextStep} />
                </div>
            )}
            {currentStep === 3 && (
                <Select>
                    {
                        nomenclaturesList.results.map((nomenclature) => (
                            <SelectItem key={nomenclature.id}>
                                {nomenclature.name}
                            </SelectItem>
                        ))
                    }
                </Select>
            )}
            {currentStep === 2 && (
                <div className="w-full max-w-xl flex flex-col gap-4">
                    <DateRangePicker
                        label="Период трансляции"
                        hideTimeZone
                        visibleMonths={2}
                        defaultValue={{
                            start: parseDate(today.toISOString().split('T')[0]),
                            end: parseDate(tomorrow.toISOString().split('T')[0])
                        }}
                        onChange={handleDateRangeChange}
                        fullWidth={false}
                        labelPlacement='outside-left'
                        radius='md'
                    />
                    <div className="flex gap-4">
                        <Input
                            type="time"
                            label="Время начала"
                            value={startTime}
                            onChange={handleStartTimeChange}
                        />
                        <Input
                            type="time"
                            label="Время окончания"
                            value={endTime}
                            onChange={handleEndTimeChange}
                        />
                    </div>
                    <ButtonBack onClick={handlePreviousStep} />
                    <ButtonForward onClick={handleSubmit}>Отправить</ButtonForward>
                </div>
            )}
        </div>
    );
}

export default CreateOrders;