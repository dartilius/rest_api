'use client'

import { Button, Form, Input, Select } from 'antd';
import styles from './NomenclatureCreate.module.scss';
import { useEffect, useState } from 'react';
import { NomenclatureCreateInterface, Day, DaySettings, SettingsInterface } from '@/shared/interface/nomenclature.interface';
import Cookies from 'js-cookie';
import { timezonesArray } from '@/shared/types/timezone';

const { Option } = Select;

interface NomenclatureCreateProps {
    data: NomenclatureCreateInterface;
}

export default function Create({ data }: NomenclatureCreateProps) {
    const [formData, setFormData] = useState<NomenclatureCreateInterface | null>(data);
    const [editMode, setEditMode] = useState<boolean>(false);

    useEffect(() => {
        if (!formData?.settings) {
            setFormData((prevData: NomenclatureCreateInterface | null) => {
                if (!prevData) return null;

                const defaultSettings: SettingsInterface = {
                    fri: { worktime: ['9', '20'], default_volume: [50, 50, 50, 50] },
                    mon: { worktime: ['9', '20'], default_volume: [50, 50, 50, 50] },
                    sat: { worktime: ['9', '20'], default_volume: [50, 50, 50, 50] },
                    sun: { worktime: ['9', '20'], default_volume: [50, 50, 50, 50] },
                    thu: { worktime: ['9', '20'], default_volume: [50, 50, 50, 50] },
                    tue: { worktime: ['9', '20'], default_volume: [50, 50, 50, 50] },
                    wed: { worktime: ['9', '20'], default_volume: [50, 50, 50, 50] }
                };

                return {
                    ...prevData,
                    settings: defaultSettings
                };
            });
        }
    }, [formData]);

    const getToken = () => {
        return Cookies.get('accessToken');
    };

    const handleTimeZoneChange = (value: string) => {
        setFormData((prevData: NomenclatureCreateInterface | null) => {
            if (!prevData) return null;
            return {
                ...prevData,
                timezone: value
            };
        });
    };

    const toggleEditMode = () => {
        setEditMode(!editMode);
    };

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = event.target;

        setFormData((prev: NomenclatureCreateInterface | null) => {
            if (prev === null) {
                return null;
            }

            return {
                ...prev,
                [name]: value
            };
        });
    };

    const handleSettingsInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = event.target;
        const [day, property] = name.split('_') as [Day, keyof DaySettings];

        setFormData((prevData: NomenclatureCreateInterface | null) => {
            if (!prevData) return null;

            const updatedSettings: SettingsInterface = {
                ...prevData.settings,
                [day]: {
                    ...prevData.settings[day],
                    [property]: property === 'worktime' ? value.split(',') as [string, string] : value.split(',').map(Number) as [number, number, number, number]
                }
            };

            return { ...prevData, settings: updatedSettings };
        });
    };

    const handleSubmit = async () => {
        if (!formData) return;

        const updatedData: NomenclatureCreateInterface = {
            name: formData.name,
            description: formData.description,
            timezone: formData.timezone,
            settings: formData.settings
        };

        if (formData.timezone !== data.timezone) {
            updatedData.timezone = formData.timezone;
        }

        const response = await fetch(`http://192.168.0.180:8000/api/nomenclatures/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `access_token ${getToken()}`
            },
            body: JSON.stringify(updatedData)
        });

        if (response.ok) {
            setEditMode(false);
        } else {
            console.error('Ошибка при сохранении');
        }
    };

    return (
        <div className={styles.container}>
            <Form layout='vertical' className={styles.form}>
                <Form.Item label='Название' name='name'>
                    <Input onChange={handleInputChange} name='name' />
                </Form.Item>
                <Form.Item label='Описание' name='description'>
                    <Input onChange={handleInputChange} name='description' />
                </Form.Item>
                <Form.Item label="timezone" name="timezone">
                    <Select placeholder='timezone' onChange={handleTimeZoneChange} style={{ width: '100%' }}>
                        {timezonesArray.map(timezone => (
                            <Option key={timezone.value} value={timezone.value}>{timezone.label}</Option>
                        ))}
                    </Select>
                </Form.Item>
                <label>Настройки</label>
                {['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'].map(day => (
                    <Form.Item label={day.charAt(0).toUpperCase() + day.slice(1)} key={day}>
                        <Input.Group compact>
                            <Input 
                                onChange={handleSettingsInputChange} 
                                name={`${day}_default_volume`} 
                                placeholder="default_volume (comma-separated)"
                            />
                            <Input 
                                onChange={handleSettingsInputChange} 
                                name={`${day}_worktime`} 
                                placeholder="worktime (comma-separated)"
                            />
                        </Input.Group>
                    </Form.Item>
                ))}
                <Button type="primary" onClick={handleSubmit}>Сохранить</Button>
            </Form>
        </div>
    );
}
