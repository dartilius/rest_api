'use client'

import { NomenclaturesService } from "@/services/nomenclatures/nomenclatures.service";
import { NomenclatureInterface } from "@/shared/interface/nomenclature.interface";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import styles from './Nomenclature.module.scss'
import { Button, Form, Input, Select, Skeleton } from "antd/lib";
import { timezonesArray } from "@/shared/types/timezone";

const { TextArea } = Input;
const { Option } = Select;


export default function Nomenclature() {
    const router = useRouter();
    const { id } = router.query;

    const [nomenclatures, setNomenclatures] = useState<NomenclatureInterface>();
    const [formData, setFormData] = useState<any | null>(nomenclatures);
    const [loading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string>('');

    useEffect(() => {
        const fetchNomenclatures = async () => {
            setIsLoading(true);
            try {
                if (id) {
                    const data: NomenclatureInterface = await NomenclaturesService.getById(id);
                    setNomenclatures(data);
                }
            } catch (error) {
                console.error('Fetch error:', error);
            }
            setIsLoading(false);
        };
        fetchNomenclatures();
    }, [id]);

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

    const handleTimeZoneChange = (value: string) => {
        setFormData((prevData: any) => ({
            ...prevData,
            timezone: value
        }));
    };

    const handleSubmit = async () => {
        const updatedData: any = {
            name: formData.name,
            description: formData.description
        };
    
        // Проверяем, изменилась ли временная зона и добавляем ее в updatedData, если да
        if (formData.timezone !== nomenclatures?.timezone) {
            updatedData.timezone = formData.timezone;
        }
    
        const response = await fetch(`http://192.168.0.180:8000/api/nomenclatures/${id}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updatedData)
        });
    
        if (response.ok) {
        } else {
            console.error('Ошибка при сохранении');
        }
    };

    return (
        <>
            {error && <p>{error}</p>}
            {loading ? (<Skeleton active={loading} />) : (
                <><div className={styles.mainContainer}>
                    <div className={styles.container}>
                        <div><strong>id: </strong>{nomenclatures?.id}</div>
                        <div><strong>Время последнего ответа: </strong>{nomenclatures?.last_answer}</div>
                        <div><strong>Версия: </strong>{nomenclatures?.version}</div>
                        <div><strong>Дата создания: </strong>{nomenclatures?.created}</div>
                        <div><strong>Создатель: </strong>{nomenclatures?.owner}</div>
                    </div> {/* Обычное описание*/}
                    <div className={styles.sideContainer}>
                        <span>Настройки</span>
                        <div className={styles.settingsContainer}>
                            <Form layout="horizontal">
                                <Form.Item label="Название" name="name">
                                    <Input defaultValue={nomenclatures?.name} onChange={handleInputChange} name="name" />
                                </Form.Item>
                                <Form.Item label="Описание" name="description">
                                    <Input defaultValue={nomenclatures?.description} name="description" onChange={handleInputChange} />
                                </Form.Item>
                                <Form.Item label="timezone" name="timezone">
                                    <Select defaultValue={nomenclatures?.timezone} onChange={handleTimeZoneChange}>
                                        {/* Отображение временных зон в компоненте Select */}
                                        {timezonesArray.map(timezone => (
                                            <Option key={timezone.value} value={timezone.value}>{timezone.label}</Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                                <Button type="primary" onClick={handleSubmit}>Сохранить</Button>
                            </Form>
                        </div>
                        <div className={styles.menu_table}>
                            <div className={styles.menu_table_row}>
                                <span></span>
                                <div className={styles.menu_table_item}>Громкость</div>
                                <div className={styles.menu_table_item}>Время</div>
                            </div>
                            <div className={styles.menu_table_row}>
                                Пн
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.mon.default_volume.join(', ')}</div>
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.mon.worktime.join(', ')}</div>
                            </div>
                            <div className={styles.menu_table_row}>
                                Вт
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.tue.default_volume.join(', ')}</div>
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.tue.worktime.join(', ')}</div>
                            </div>
                            <div className={styles.menu_table_row}>
                                Ср
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.wed.default_volume.join(', ')}</div>
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.wed.worktime.join(', ')}</div>
                            </div>
                            <div className={styles.menu_table_row}>
                                Чт
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.thu.default_volume.join(', ')}</div>
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.thu.worktime.join(', ')}</div>
                            </div>
                            <div className={styles.menu_table_row}>
                                Пт
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.fri.default_volume.join(', ')}</div>
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.fri.worktime.join(', ')}</div>
                            </div>
                            <div className={styles.menu_table_row}>
                                Сб
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.sat.default_volume.join(', ')}</div>
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.sat.worktime.join(', ')}</div>
                            </div>
                            <div className={styles.menu_table_row}>
                                Вс
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.sun.default_volume.join(', ')}</div>
                                <div className={styles.menu_table_item}>{nomenclatures?.settings.sun.worktime.join(', ')}</div>
                            </div>
                        </div> {/* settings json*/}
                    </div> {/*Название, описание, timezone*/}
                </div><div></div></>
            )}
            
        </>
    );
}
