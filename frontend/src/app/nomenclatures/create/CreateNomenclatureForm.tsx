'use client'; // Указывает, что компонент является клиентским

import React, { useState } from 'react';
import {API_URL} from "@/src/config/api.config";
import {getTokenStorage} from "@/src/services/auth/auth.helper";
import {Button, Input} from "@nextui-org/react";
import styles from './CreateNomenclature.module.scss'

type DaySettings = {
    worktime: string;
    default_volume: string;
};

type FormData = {
    name: string;
    description: string;
    status: number;
    version: string;
    timezone: string;
    settings: {
        mon: DaySettings;
        tue: DaySettings;
        wed: DaySettings;
        thu: DaySettings;
        fri: DaySettings;
        sat: DaySettings;
        sun: DaySettings;
    };
};

const timeOptions = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30",
    "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
    "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30",
    "21:00", "21:30", "22:00", "22:30", "23:00", "23:30"
];

export default function CreateNomenclatureForm() {
    const token = getTokenStorage();
    const [hint, setHint] = useState<string | null>(null);
    const [formData, setFormData] = useState<FormData>({
        name: '',
        description: '',
        status: 0,
        version: '',
        timezone: '',
        settings: {
            mon: { worktime: '', default_volume: '' },
            tue: { worktime: '', default_volume: '' },
            wed: { worktime: '', default_volume: '' },
            thu: { worktime: '', default_volume: '' },
            fri: { worktime: '', default_volume: '' },
            sat: { worktime: '', default_volume: '' },
            sun: { worktime: '', default_volume: '' },
        },
    });

    // const handleSettingsChange = (day: keyof FormData['settings'], field: keyof DaySettings, value: string) => {
    //     setFormData((prevState) => ({
    //         ...prevState,
    //         settings: {
    //             ...prevState.settings,
    //             [day]: { ...prevState.settings[day], [field]: value },
    //         },
    //     }));
    // };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        // Преобразование settings в нужный формат
        const serializedSettings = Object.fromEntries(
            Object.entries(formData.settings).map(([day, settings]) => [
                day,
                JSON.stringify(settings),
            ])
        );

        const finalData = {
            ...formData,
            settings: serializedSettings,
        };

        try {
            const response = await fetch(`${API_URL}/nomenclatures/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `access_token ${token}`
                },
                body: JSON.stringify(finalData),
            });

            if (!response.ok) {
                throw new Error('Error creating nomenclature');
            }

            alert('Nomenclature created successfully');
        } catch (error: any) {
            alert(`Error: ${error.message}`);
        }
    };

    const handleChange = (e: any) => {
        const { name, value } = e.target;
        setFormData((prevState) => ({
            ...prevState,
            [name]: value,
        }));
    };
    //
    // const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, '0'));
    // const minutes = Array.from({ length: 60 }, (_, i) => i.toString().padStart(2, '0'));
    //
    // const generateWorktime = (startHour: string, startMinute: string, endHour: string, endMinute: string) => {
    //     return `(("(${startHour}:${startMinute})", "(${endHour}:${endMinute})"))`;
    // };



    // const handleWorktimeChange = (
    //     day: keyof typeof formData['settings'],
    //     startHour: string,
    //     startMinute: string,
    //     endHour: string,
    //     endMinute: string
    // ) => {
    //     const worktime = generateWorktime(startHour, startMinute, endHour, endMinute);
    //     handleSettingsChange(day, 'worktime', worktime);
    // };


    const [startHour, setStartHour] = useState<string>('00');
    const [startMinute, setStartMinute] = useState<string>('00');
    const [endHour, setEndHour] = useState<string>('00');
    const [endMinute, setEndMinute] = useState<string>('00');

    const handleSettingsChange = (
        day: keyof typeof formData['settings'],
        field: keyof typeof formData['settings']['mon'],
        value: string
    ) => {
        setFormData((prevState) => ({
            ...prevState,
            settings: {
                ...prevState.settings,
                [day]: { ...prevState.settings[day], [field]: value },
            },
        }));
    };

    const copyFirstDaySettings = () => {
        const firstDay = formData.settings.mon;
        setFormData((prevState) => ({
            ...prevState,
            settings: Object.keys(prevState.settings).reduce((acc, day) => {
                acc[day as keyof typeof prevState.settings] = { ...firstDay };
                return acc;
            }, {} as typeof prevState.settings),
        }));
    };

    const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, '0'));
    const minutes = Array.from({ length: 60 }, (_, i) => i.toString().padStart(2, '0'));

    const handleWorktimeChange = (day: keyof typeof formData['settings']) => {
        const worktime = `((${startHour},${startMinute}),(${endHour},${endMinute}))`;
        handleSettingsChange(day, 'worktime', worktime);
    };

    return (
        <form onSubmit={handleSubmit}>
            <div className={styles.description}>
                <label className={styles.field}>
                    Название:
                    <Input type="text" name="name" value={formData.name} onChange={handleChange} required/>
                </label>
                <label className={styles.field}>
                    Описание:
                    <Input type="text" name="description" value={formData.description} onChange={handleChange}/>
                </label>
                <label className={styles.field}>
                    Версия:
                    <Input type="text" name="version" value={formData.version} onChange={handleChange} required/>
                </label>
                <label className={styles.field}>
                    Часовой пояс:
                    <Input type="text" name="timezone" value={formData.timezone} onChange={handleChange}/>
                </label>
            </div>
            {Object.keys(formData.settings).map((day) => (
                <div key={day} className="settings">
                    <h3>{day.toUpperCase()}</h3>
                    <label className="field">
                        Время работы:
                        <div>
                            <span>С: </span>
                            <select
                                value={startHour}
                                onChange={(e) => {
                                    setStartHour(e.target.value);
                                    handleWorktimeChange(day as keyof typeof formData.settings);
                                }}
                            >
                                {hours.map((hour) => (
                                    <option key={hour} value={hour}>
                                        {hour}
                                    </option>
                                ))}
                            </select>
                            <select
                                value={startMinute}
                                onChange={(e) => {
                                    setStartMinute(e.target.value);
                                    handleWorktimeChange(day as keyof typeof formData.settings);
                                }}
                            >
                                {minutes.map((minute) => (
                                    <option key={minute} value={minute}>
                                        {minute}
                                    </option>
                                ))}
                            </select>
                            <span> По: </span>
                            <select
                                value={endHour}
                                onChange={(e) => {
                                    setEndHour(e.target.value);
                                    handleWorktimeChange(day as keyof typeof formData.settings);
                                }}
                            >
                                {hours.map((hour) => (
                                    <option key={hour} value={hour}>
                                        {hour}
                                    </option>
                                ))}
                            </select>
                            <select
                                value={endMinute}
                                onChange={(e) => {
                                    setEndMinute(e.target.value);
                                    handleWorktimeChange(day as keyof typeof formData.settings);
                                }}
                            >
                                {minutes.map((minute) => (
                                    <option key={minute} value={minute}>
                                        {minute}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </label>
                    <label className="field">
                        Стандартная громкость:
                        <input
                            type="text"
                            value={formData.settings[day as keyof typeof formData.settings].default_volume}
                            onChange={(e) =>
                                handleSettingsChange(day as keyof typeof formData.settings, 'default_volume', e.target.value)
                            }
                            required
                        />
                    </label>
                </div>
            ))}
            <button type="button" onClick={copyFirstDaySettings}>
                Копировать настройки с первого дня на остальные
            </button>
            <Button variant='solid' color='primary' type="submit" style={{width: '320px'}}>Создать</Button>

        </form>
    );
}

