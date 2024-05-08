import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import Custom500 from "@/pages/500";
import { NomenclatureInterface } from "@/shared/interface/nomenclature.interface";
import { GetServerSideProps, InferGetServerSidePropsType } from "next";
import { useRouter } from "next/router";
import styles from '../Nomenclatures.module.scss'
import { Form, Input, Button, Select, List, Typography } from "antd/lib";
import { useState } from "react";

const { TextArea } = Input;


interface NomenclatureProps {
    data: NomenclatureInterface | null; // Изменяем тип данных на единичный объект
    error?: string;
}

export const getServerSideProps: GetServerSideProps<NomenclatureProps> = async ({ params }) => {
    const { id } = params || {}; // Добавляем проверку на существование params

    try {
        if (!id) {
            throw new Error('ID is missing');
        }

        const res = await fetch(`http://192.168.0.170:8000/api/nomenclatures/${id}/`);
        
        if (!res.ok) {
            throw new Error('Failed to fetch data');
        }
    
        const data: NomenclatureInterface = await res.json(); // Ожидаем единичный объект, а не массив
        
        return {
            props: {
                data: data,
            },
        };
    } catch (error: Error | any) {
        return {
            props: {
                data: null,
                error: error.message
            }
        };
    }
};

export default function Nomenclature({ data, error }: InferGetServerSidePropsType<typeof getServerSideProps>) {
    const router = useRouter();
    const [edit, setEdit] = useState(false);
    const { id } = router.query;
    
    if (error) {
        console.log(error);
        
        return <Custom500 />;
    }

    if (!data) {
        // Если данные отсутствуют, отображаем сообщение об этом
        return <div>Нет данных</div>;
    }

    console.log(data);
    
    return (
        <>
            <div className={styles.breadcrumb}>
                <Breadcrumb>
                    <BreadcrumbList>
                        <BreadcrumbItem>
                            <BreadcrumbLink href="/">Главная</BreadcrumbLink>
                        </BreadcrumbItem>
                        <BreadcrumbSeparator />
                        <BreadcrumbItem>
                            <BreadcrumbLink href="/nomenclatures/">Номенклатуры</BreadcrumbLink>
                        </BreadcrumbItem>
                        <BreadcrumbSeparator />
                        <BreadcrumbItem>
                            <BreadcrumbLink href={`/nomenclatures/${id}`}>
                                <BreadcrumbPage>
                                    Номенклатура {data.name}
                                </BreadcrumbPage>
                            </BreadcrumbLink>
                        </BreadcrumbItem>
                    </BreadcrumbList>
                </Breadcrumb>
            </div>

            
            <Button onClick={() => setEdit(!edit)}>Редактировать</Button>
            <Form
                labelCol={{ span: 4 }} 
                wrapperCol={{ span: 14 }} 
                layout="horizontal"
                style={{display: 'flex', justifyContent: 'center', flexDirection: 'column', marginTop: '48px'}} 
                disabled={!edit}
            >
                <Form.Item label="Название" initialValue={data.name}>
                    <Input defaultValue={data.name}/>
                </Form.Item>
                <Form.Item label="Описание" initialValue={data.description}>
                    <TextArea defaultValue={data.description}/>
                </Form.Item>
                <Form.Item label="Статус" initialValue={data.status}>
                    <Input value={data.status} disabled/>
                </Form.Item>
                <Form.Item label="Версия" initialValue={data.version}>
                    <Input value={data.version}/>
                </Form.Item>
            </Form>


            <div style={{display: 'flex', justifyContent: 'center', flexDirection: 'column', marginTop: '48px'}}>
                <Button onClick={() => setEdit(!edit)}>Редактировать</Button>
                
                <label style={{fontSize: '24px'}}><strong>Владелец</strong></label>
                <Form
                    labelCol={{ span: 4 }} 
                    wrapperCol={{ span: 14 }} 
                    layout="horizontal"
                    disabled={!edit}
                >
                    <Form.Item label="Фамилия" initialValue={data.owner}>
                        <Input value={data.owner.last_name}/>
                    </Form.Item>
                    <Form.Item label="Имя" initialValue={data.owner}>
                        <Input value={data.owner.first_name}/>
                    </Form.Item>
                    <Form.Item label="Отчество" initialValue={data.owner}>
                        <Input value={data.owner.middle_name}/>
                    </Form.Item>
                </Form>
            </div>
        </>
    );
}
