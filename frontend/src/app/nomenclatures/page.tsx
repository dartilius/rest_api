'use client'

import { useEffect, useState } from "react";
import { Button, Select, Skeleton, Typography, Input } from "antd/lib";
import { NomenclaturesService } from "@/services/nomenclatures/nomenclatures.service";
import { NomenclatureListResponseInterface } from "@/shared/interface/nomenclature.interface";
import styles from './Nomenclature.module.scss'
import Link from "next/link";

const { Search } = Input;

export default function Nomenclatures() {
    const [nomenclatures, setNomenclatures] = useState<NomenclatureListResponseInterface>();
    const [error, setError] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [limit, setLimit] = useState<number>(10)
    const [search, setSearch] = useState<string>('')
    const results = nomenclatures?.results

    useEffect(() => {
        fetchNomenclatures(currentPage, limit, search);
    }, [currentPage, limit, search]);

    const fetchNomenclatures = async (page: number, limit: number, search: string) => {
        setIsLoading(true);
        try {
            const data = await NomenclaturesService.getAll({ page, limit, search });
            setNomenclatures(data);
            setError('');
        } catch (error) {
            console.error('Fetch error:', error);
            setError('Failed to fetch data');
        }
        setIsLoading(false);
    };

    const nextPage = () => {
        if (nomenclatures?.next) {
            setCurrentPage(currentPage + 1);
        }
    }

    const prevPage = () => {
        if (nomenclatures?.previous) {
            setCurrentPage(currentPage - 1);
        }
    }

    const handleLimitChange = (value: number) => {
        setLimit(value)
    }

    const handleSearchChange = (value: string) => {
        setSearch(value)
    }

    return (
        <div >
            {error && <p>{error}</p>}
            {isLoading ? (
                <Skeleton active={isLoading} />
            ) : (
                <div className={styles.container}>
                    <div className={styles.container_left}>
                        <div className={styles.container_left_limit}>
                            <Typography.Text type="secondary">Лимит:</Typography.Text>
                            <Select value={limit} style={{ width: 200 }} onChange={handleLimitChange}>
                                <Select.Option value={10}>10</Select.Option>
                                <Select.Option value={25}>25</Select.Option>
                                <Select.Option value={50}>50</Select.Option>
                                <Select.Option value={100}>100</Select.Option>
                            </Select>
                        </div>
                        <div className={styles.container_left_search}>
                        <Typography.Text type="secondary">Поиск:</Typography.Text>
                            <Search
                                enterButton
                                style={{ width: 200 }}
                                allowClear
                                defaultValue={search}
                                value={search === '' ? undefined : search} 
                                onSearch={handleSearchChange}
                            />
                        </div>
                        <div className={styles.container_left_search}>
                        <Typography.Text type="secondary">Версия:</Typography.Text>
                            <Search
                                enterButton
                                style={{ width: 200 }}
                                allowClear
                                defaultValue={search}
                                value={search === '' ? undefined : search} 
                            />
                        </div>
                        <div className={styles.container_left_search}>
                        <Typography.Text type="secondary">Статус:</Typography.Text>
                            <Search
                                enterButton
                                style={{ width: 200 }}
                                allowClear
                                defaultValue={search}
                                value={search === '' ? undefined : search} 
                            />
                        </div>
                        <div className={styles.container_left_search}>
                            <Button
                                type="primary"
                                style={{width: '100%'}}
                            >
                                <Link
                                    href={`/nomenclatures/create`}
                                    // rel="noopener noreferrer"
                                    target="_blank"
                                >
                                    Создать
                                </Link>
                            </Button>
                        </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection:'column' }}>
                        <div className={styles.menu_table}>
                            <div className={styles.menu_table_row}>
                            <div className={styles.menu_table_item}>Наименование</div>
                            <div className={styles.menu_table_item}>Часовой пояс</div>
                            <div className={styles.menu_table_item}>Последнее время ответа</div>
                            <div className={styles.menu_table_item}>Версия</div>
                        </div>
                            {results?.map(el => (
                                <div className={styles.menu_table_row_color} key={el.id}>
                                    <div className={styles.menu_table_item}>
                                        <Link
                                            href={`/nomenclatures/${el.id}`}
                                            // rel="noopener noreferrer"
                                            target="_blank"
                                        >
                                            {el.name}
                                        </Link>
                                    </div>
                                    <div className={styles.menu_table_item}>{el.timezone}</div>
                                    <div className={styles.menu_table_item}>{el.last_answer}</div>
                                    <div className={styles.menu_table_item}>{el.version}</div>
                                </div>
                            ))}
                        </div>
                        <div className={styles.buttons}>
                            <Button disabled={!nomenclatures?.previous} onClick={prevPage}>Prev</Button>
                            <Button disabled={!nomenclatures?.next} onClick={nextPage}>Next</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
