'use client';

import { ChangeEvent, useState } from 'react';
import { Input, ButtonForward, ButtonBack } from '@/src/components/ui';

function CreateOrders() {
    const [inputValues, setInputValues] = useState({
        name: '',
        description: '',
        details: ''
    });
    const [currentStep, setCurrentStep] = useState(1);

    const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
        const { name, value } = event.target;
        setInputValues((prevValues) => ({
            ...prevValues,
            [name]: value
        }));
    };

    const handleNextStep = () => {
        if (currentStep < 2) setCurrentStep((prevStep) => prevStep + 1);
    };

    const handlePreviousStep = () => {
        if (currentStep > 1) setCurrentStep((prevStep) => prevStep - 1);
    };

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

            {currentStep === 2 && (
                <div>
                    <Input
                        required
                        name="details"
                        placeholder="Введите детали"
                        label="Детали*"
                        onChange={handleInputChange}
                        value={inputValues.details}
                    />
                    <ButtonBack onClick={handlePreviousStep} />
                    <ButtonForward onClick={() => console.log(inputValues)}>Создать</ButtonForward>
                </div>
            )}

            <p>Текущие значения: {JSON.stringify(inputValues)}</p>
        </div>
    );
}

export default CreateOrders;
