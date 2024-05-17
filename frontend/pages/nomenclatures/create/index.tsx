import { Button, Form, Input, Select } from 'antd/lib'
import styles from './NomenclatureCreate.module.scss'
import { timezonesArray } from '@/shared/type/timezone'
import { useEffect, useState } from 'react';
import Cookies from 'js-cookie'
import {NomenclatureCreateInterface} from "@/shared/interface/Nomenclature.interface";
import { NomenclaturesService } from '@/services/nomenclatures/nomenclatures.service';

const { Option } = Select;

interface NomenclatureCreateProps {
    data: NomenclatureCreateInterface
}

export default function Create({data}: NomenclatureCreateProps) {

    const [formData, setFormData] = useState<any | null>(data);
    const [editMode, setEditMode] = useState<boolean>(false);

    useEffect(() => {
        if (!formData?.settings) {
            setFormData((prevData: any) => ({
                ...prevData,
                settings: {
                    "fri": "{\"worktime\": \"((9,), (20,))\", \"default_volume\": \"(50, 50, 50, 50)\"}",
                    "mon": "{\"worktime\": \"((9,), (20,))\", \"default_volume\": \"(50, 50, 50, 50)\"}",
                    "sat": "{\"worktime\": \"((9,), (20,))\", \"default_volume\": \"(50, 50, 50, 50)\"}",
                    "sun": "{\"worktime\": \"((9,), (20,))\", \"default_volume\": \"(50, 50, 50, 50)\"}",
                    "thu": "{\"worktime\": \"((9,), (20,))\", \"default_volume\": \"(50, 50, 50, 50)\"}",
                    "tue": "{\"worktime\": \"((9,), (20,))\", \"default_volume\": \"(50, 50, 50, 50)\"}",
                    "wed": "{\"worktime\": \"((9,), (20,))\", \"default_volume\": \"(50, 50, 50, 50)\"}"
                }
            }));
        }
    }, [formData]);

    const getToken = () => {
        return Cookies.get('accessToken');
    }

    const handleTimeZoneChange = (value: string) => {
        setFormData((prevData: any) => ({
            ...prevData,
            timezone: value
        }));
    };

    const toggleEditMode = () => {
        setEditMode(!editMode);
    };

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = event.target;
    
        setFormData((prev: { [x: string]: any; } | null) => {
            if (prev === null) {
                return null;
            }
    
            return {
                ...prev,
                [name]: value || prev[name]
            };
        });
    };

    const handleSettingsInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = event.target;
    
        // Parse the input name to extract the day and property
        const [day, property] = name.split('_');
        
        // Update the settings object based on the day and property
        setFormData((prevData: any) => ({
            ...prevData,
            settings: {
                ...prevData.settings,
                [day]: {
                    ...prevData.settings[day],
                    [property]: value
                }
            }
        }));
    };
    

    const handleSubmit = async () => {
        const updatedData: any = {
            name: formData.name,
            description: formData.description,
            timezone: formData.timezone,
            settings: formData.settings
        };

        const token = getToken()
    
        // Проверяем, изменилась ли временная зона и добавляем ее в updatedData, если да
        if (formData.timezone !== data?.timezone) {
            updatedData.timezone = formData.timezone;
        }

        NomenclaturesService.create(updatedData, token)
    
        // const response = await fetch(`http://192.168.0.180:8000/api/nomenclatures/`, {
        //     method: 'Post',
        //     headers: {
        //         'Content-Type': 'application/json',
        //         'Authorization': `access_token ${getToken()}` // Invoke getToken to get the token
        //     },
        //     body: JSON.stringify(updatedData)
        // });

    };

  return (
    <div className={styles.container}>
        <Form layout='vertical' className={styles.form}>
            <Form.Item label='Название' name='name'>
                <Input onChange={handleInputChange} name='name'/>
            </Form.Item>
            <Form.Item label='Описание' name='description'>
                <Input onChange={handleInputChange} name='description'/>
            </Form.Item>
            <Form.Item label="timezone" name="timezone">
                <Select placeholder='timezone' onChange={handleTimeZoneChange} style={{ width: '100%' }}>
                    {/* Отображение временных зон в компоненте Select */}
                    {timezonesArray.map(timezone => (
                        <Option key={timezone.value} value={timezone.value}>{timezone.label}</Option>
                    ))}
                </Select>
            </Form.Item>
            <label>Настройки</label>
            <Form.Item label='Пн'>
                <Input.Group compact>
                    <Input onChange={handleSettingsInputChange} name='mon_default_volume' />
                    <Input onChange={handleSettingsInputChange} name='mon_worktime' />
                </Input.Group>
            </Form.Item>

            <Button type="primary" onClick={handleSubmit}>Сохранить</Button>
        </Form>
    </div>
  )
}