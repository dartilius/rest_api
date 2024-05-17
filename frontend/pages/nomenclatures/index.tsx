import styles from './Nomenclatures.module.scss';
import Custom500 from '../500';
import { Button, Input, Pagination, Select } from 'antd/lib';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { AuthService } from '@/services/auth/auth.service';
import Link from 'next/link';
import { timezonesArray } from '@/shared/type/timezone';
import { NomenclatureListResponseInterface } from "@/shared/interface/Nomenclature.interface";
import { NomenclaturesService } from '@/services/nomenclatures/nomenclatures.service';
import Error from 'next/error';

const { Search } = Input;
const { Option } = Select;

interface INomenclaturesProps {
    data: NomenclatureListResponseInterface | null
    error?: string
}

export default function Nomenclatures() {
    const router = useRouter();
    const [limit, setLimit] = useState(10); // Установка limit по умолчанию в 10
    const [page, setPage] = useState(1); // Установка page по умолчанию в 1
    const [searchValue, setSearchValue] = useState('');
    const [version, setVersion] = useState('');
    const [timezone, setTimezone] = useState('');
    const [nomenclatures, setNomenclatures] = useState<NomenclatureListResponseInterface>();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchNomenclatures = async () => {
            try {
                const data: NomenclatureListResponseInterface = await NomenclaturesService.get();
                setNomenclatures(data);
            } catch (err) {
                if (err instanceof Error) {
                    setError('какая-то ошибка');
                } else {
                    setError('Неизвестная ошибка');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchNomenclatures();
    }, []);

    
    
    useEffect(() => {
        const handleRouteChange = () => {
            setPage(parseInt(router.query.page as string) || 1);
            setLimit(parseInt(router.query.limit as string) || 10);
            setSearchValue(decodeURIComponent(router.query.name as string || ''));
            setVersion(router.query.version as string || '');
            setTimezone(router.query.timezone as string || '');
        };

        router.events.on('routeChangeComplete', handleRouteChange);
        return () => {
            router.events.off('routeChangeComplete', handleRouteChange);
        };
    }, [router.events, router.query]);    

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    const updateFilters = (filters: { [key: string]: string }, searchValueToUpdate?: string) => {
        if (!searchValueToUpdate) {
            return
        }
        setSearchValue(searchValueToUpdate); // Обновляем searchValue перед установкой новых фильтров
        const newQuery: any = {
            limit,
            page,
            name__icontains: encodeURIComponent(searchValueToUpdate.trim()), // Используем переданное значение searchValueToUpdate
            version__icontains: encodeURIComponent(version),
            timezone__iexact: encodeURIComponent(timezone),
            // status: encodeURIComponent(status)
        };
    
        Object.keys(filters).forEach(key => {
            if (newQuery.hasOwnProperty(key)) {
                newQuery[key] = encodeURIComponent(filters[key]);
            }
        });
    
        const queryString = Object.entries(newQuery)
            .filter(([_, value]) => value)
            .map(([key, value]) => `${key}=${value}`)
            .join('&');
    
        router.push(`/nomenclatures?${queryString}`);
    };
    
    const handleSearchEnter = (value: string) => {
        setSearchValue(value); // Обновляем searchValue
        updateFilters({ name__icontains: value }); // Передаем новое значение searchValue для обновления фильтров
    };
    
    const handleVersionChange = (value: string) => {
        setVersion(value); // Обновляем version
        updateFilters({ version__icontains: value }); // Передаем новое значение version для обновления фильтров
    };

    const handleTimeZoneChange = (newTimeZone: string) => {
        setTimezone(newTimeZone);
        updateFilters({ timezone__iexact: newTimeZone }, newTimeZone);
    };
    // const handleStatusChange = (newStatus: string) => {
    //     updateFilters({ status: newStatus });
    // };

    const handlePageChange = (newPage: number, pageSize?: number) => {
        updateFilters({ page: newPage.toString(), limit: pageSize?.toString() || limit.toString() });
    };

    const logOut = () => {
        AuthService.logout();
        router.push('/login');
    };

    return (
        <div>        
            <div className={styles.cont}>
            <div className={styles.filter}>
                    <Search
                        placeholder="Поиск по наименованию"
                        onSearch={value => handleSearchEnter(value)} // Передаем значение в handleSearchEnter
                        onChange={e => setSearchValue(e.target.value)} // Устанавливаем значение searchValue
                        value={searchValue}
                        style={{ width: '100%' }}
                    />
                    <Search
                        placeholder="Поиск по версиям"
                        onSearch={value => handleVersionChange(value)} // Передаем значение в handleVersionChange
                        onChange={e => setVersion(e.target.value)} // Устанавливаем значение version
                        value={version}
                        style={{ width: '100%' }}
                    />

                    {/* <Select
                        placeholder='Выберите статус'
                        onSelect={handleStatusChange}
                        onChange={e => handleStatusChange(e)}
                        options={[
                            { value: 'null', label: 'Все' },
                            { value: '0', label: 'доступно' },
                            { value: '1', label: 'недоступно меньше часа' },
                            { value: '2', label: 'недоступно больше часа' },
                        ]}
                        style={{ width: '100%' }}
                    /> */}
                    <Select
                        placeholder='Выберите часовой пояс'
                        value={timezone}
                        onChange={(e) => handleTimeZoneChange(e)}
                        style={{ width: '100%' }}
                    >
                        {timezonesArray.map(tz => (
                            <Option key={tz.value} value={tz.value}>{tz.label}</Option>
                        ))}
                    </Select>
                    <Button onClick={logOut} style={{ width: '100%' }}>
                        Выйти
                    </Button>
                    <Button><Link href={`/nomenclatures/create`} rel="noopener noreferrer" target="_blank">Создать</Link></Button>
                </div>
                <div className={styles['menu-table']}>
                    <div className={styles['menu-table_row']}>
                        <div className={styles['menu-table_item']}>Наименование</div>
                        <div className={styles['menu-table_item']}>Часовой пояс</div>
                        <div className={styles['menu-table_item']}>Последнее время ответа</div>
                        <div className={styles['menu-table_item']}>Версия</div>
                    </div>
                    {nomenclatures?.results.map(el => (
                        <div className={styles['menu-table_row']} key={el.id}>
                            <div className={styles['menu-table_item']}><Link href={`/nomenclatures/${el.id}`} rel="noopener noreferrer" target="_blank">{el.name}</Link></div> 
                            <div className={styles['menu-table_item']}>{el.timezone}</div>
                            <div className={styles['menu-table_item']}>{el.last_answer}</div>
                            <div className={styles['menu-table_item']}>{el.version}</div>
                        </div>
                    ))}
                    <div style={{ display: 'flex', flexDirection: 'row', gap: '24px', alignItems: 'center', justifyContent: 'center', marginTop: '48px' }}>
                        Общее кол-во: {nomenclatures?.count}
                        <Pagination
                            current={parseInt(router.query.page as string) || 1}
                            pageSize={parseInt(router.query.limit as string) || 10}
                            total={nomenclatures?.count}
                            onChange={handlePageChange}
                            showSizeChanger
                            onShowSizeChange={handlePageChange}
                            pageSizeOptions={['10', '25', '50', '100']}
                            style={{ display: 'flex', justifyContent: 'center' }}
                        />
                    </div>
                {/* <button onClick={logOut}>Выход</button> */}
                </div>
                
            
            </div>
            </div>
    );
};