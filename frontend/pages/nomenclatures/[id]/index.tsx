import Custom500 from "@/pages/500";
import { NomenclatureInterface } from "@/shared/interface/nomenclature.interface";
import { GetServerSideProps, InferGetServerSidePropsType } from "next";
import { useRouter } from "next/router";
import styles from './Nomenclature.module.scss'
import { useState } from "react";
import { Button, Form, Input, Select } from "antd/lib";
import { timezonesArray } from "@/shared/type/timezone";

const { TextArea } = Input;
const { Option } = Select;


interface NomenclatureProps {
    data: NomenclatureInterface | null;
    error?: string | null;
}

export const getServerSideProps: GetServerSideProps<NomenclatureProps> = async ({ params }) => {
    const { id } = params || {};
    
    try {
        if (!id) {
            throw new Error('ID is missing');
        }
        const res = await fetch(`http://192.168.0.180:8000/api/nomenclatures/${id}/`);
        
        if (!res.ok) {
            throw new Error('Failed to fetch data');
        }
    
        const data: NomenclatureInterface = await res.json(); // Ожидаем единичный объект, а не массив
        
        return {
            props: {
                data: data,
                error: null,
            },
        };
    } catch (error: Error | any) {
        return {
            props: {
                data: null,
                error: error.message,
            },
        };
    }
};

export default function Nomenclature({ data, error }: InferGetServerSidePropsType<typeof getServerSideProps>) {

    const router = useRouter();
    const { id } = router.query;
    const [formData, setFormData] = useState<any | null>(data);
    const [editMode, setEditMode] = useState<boolean>(false);


    if (error) return <Custom500 />;
    if (!data) return <div>Нет данных</div>;

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
    


    const toggleEditMode = () => {
        setEditMode(!editMode);
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
        if (formData.timezone !== data.timezone) {
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
            setEditMode(false);
        } else {
            console.error('Ошибка при сохранении');
        }
    };
    
    
    
    return (
        <>
            <div className={styles.mainContainer}>
                <div className={styles.container}>
                    <div><strong>id: </strong>{data.id}</div>
                    <div><strong>Время последнего ответа: </strong>{data.last_answer}</div>    
                    <div><strong>Версия: </strong>{data.version}</div>    
                    <div><strong>Дата создания: </strong>{data.created}</div>    
                    <div><strong>Создатель: </strong>{data.owner}</div>    
                </div> {/* Обычное описание*/}
                <div className={styles.sideContainer}>
                    <span>Настройки</span>
                    <div className={styles.settingsContainer}>
                        <Form layout="horizontal">
                            <Form.Item label="Название" name="name">
                                <Input defaultValue={data.name} onChange={handleInputChange} name="name"/>
                            </Form.Item>
                            <Form.Item label="Описание" name="description">
                                <Input defaultValue={data.description} name="description" onChange={handleInputChange}/>
                            </Form.Item>
                            <Form.Item label="timezone" name="timezone">
                                <Select defaultValue={data.timezone} onChange={handleTimeZoneChange}>
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
                            <div className={styles.menu_table_item}>{data.settings.mon.default_volume.join(', ')}</div>
                            <div className={styles.menu_table_item}>{data.settings.mon.worktime.join(', ')}</div>
                        </div>
                        <div className={styles.menu_table_row}>
                            Вт
                            <div className={styles.menu_table_item}>{data.settings.tue.default_volume.join(', ')}</div>
                            <div className={styles.menu_table_item}>{data.settings.tue.worktime.join(', ')}</div>
                        </div>
                        <div className={styles.menu_table_row}>
                            Ср
                            <div className={styles.menu_table_item}>{data.settings.wed.default_volume.join(', ')}</div>
                            <div className={styles.menu_table_item}>{data.settings.wed.worktime.join(', ')}</div>
                        </div>
                        <div className={styles.menu_table_row}>
                            Чт
                            <div className={styles.menu_table_item}>{data.settings.thu.default_volume.join(', ')}</div>
                            <div className={styles.menu_table_item}>{data.settings.thu.worktime.join(', ')}</div>
                        </div>
                        <div className={styles.menu_table_row}>
                            Пт
                            <div className={styles.menu_table_item}>{data.settings.fri.default_volume.join(', ')}</div>
                            <div className={styles.menu_table_item}>{data.settings.fri.worktime.join(', ')}</div>
                        </div>
                        <div className={styles.menu_table_row}>
                            Сб
                            <div className={styles.menu_table_item}>{data.settings.sat.default_volume.join(', ')}</div>
                            <div className={styles.menu_table_item}>{data.settings.sat.worktime.join(', ')}</div>
                        </div>
                        <div className={styles.menu_table_row}>
                            Вс
                            <div className={styles.menu_table_item}>{data.settings.sun.default_volume.join(', ')}</div>
                            <div className={styles.menu_table_item}>{data.settings.sun.worktime.join(', ')}</div>
                        </div>
                    </div> {/* settings json*/}
                </div> {/*Название, описание, timezone*/}
            </div>
            <div></div> {/* hw_info json*/}
        </>
    );
    
}
