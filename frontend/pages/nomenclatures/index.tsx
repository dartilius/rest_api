import { API_URL } from '@/config/api.config';
import { GetServerSideProps } from 'next';
import styles from './Nomenclatures.module.scss';
import Custom500 from '../500';
import { Input, Pagination, Select } from 'antd/lib';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { NomenclatureListResponseInterface } from '@/shared/interface/nomenclature.interface';
import { AuthService } from '@/services/auth/auth.service';
import Link from 'next/link';
import { timezonesArray } from '@/shared/type/timezone';

const { Search } = Input;
const { Option } = Select;

interface INomenclaturesProps {
    data: NomenclatureListResponseInterface | null
    error?: string
    searchValue: string
    status: string
    version: string
    timezone: string
}

type Status = 0 | 1 | 2;

// 10 25 50 100

export default function Nomenclatures({data, error}: INomenclaturesProps) {
    
    const router = useRouter()
    const [limit, setLimit] = useState(router.query.limit || 10)
    const [page, setPage] = useState(router.query.page || 1)

    const [searchValue, setSearchValue] = useState('');
    const [status, setStatus] = useState('');
    const [version, setVersion] = useState('');
    const [timezone, setTimezone] = useState('');

    // useEffect(() => {
    //     if (router.isReady) {
    //         setLimit(parseInt(router.query.limit as string) || 10);
    //         setPage(parseInt(router.query.page as string) || 1);
    //         setStatus('null');
    //         setSearchValue('');
    //     }
    // }, [router.isReady, router.query.limit, router.query.page, router.query.status, router.query.name]);    

    useEffect(() => {
        const initialPath = router.asPath; // Сохраняем начальный путь при монтировании компонента
    
        // Функция для проверки обновления страницы
        const checkPageReload = () => {
            if (window.location.pathname !== initialPath) {
                router.replace(
                    {
                        pathname: router.pathname,
                        query: {}, // Очищаем параметры запроса
                    },
                    undefined,
                    { shallow: true }
                );
            }
        };
    
        // Проверяем обновление страницы при каждом изменении маршрута
        const handleRouteChange = (url: string) => {
            if (url !== initialPath) {
                checkPageReload();
            }
        };
    
        // Проверяем обновление страницы после монтирования компонента
        checkPageReload();
    
        // Добавляем слушателя для проверки обновления страницы при каждом изменении маршрута
        router.events.on('routeChangeComplete', handleRouteChange);
    
        // Очищаем слушателя при размонтировании компонента
        return () => {
            router.events.off('routeChangeComplete', handleRouteChange);
        };
    }, [router]);
    
    

    if (error || !data) {
        return <Custom500 />
    }

    console.log(data);

    const handleSearchChange = (value: string) => {
        setSearchValue(value);
    };
    const handleStatusEnter = (value: string) => {
        setStatus(value);
    };
    
    const handleSearchEnter = () => {
        const trimmedValue = searchValue.trim();
        if (trimmedValue !== '') {
            router.push(`/nomenclatures?limit=${limit}&page=${page}&name=${encodeURIComponent(trimmedValue)}`);
        } else {
            router.push(`/nomenclatures?limit=${limit}&page=${page}`);
        }
    };

    const handleStatusChange = (status: string) => {
        const newStatus = status
        setStatus(newStatus);
        router.push(`/nomenclatures?limit=${limit}&page=${page}&status=${newStatus}&name=${encodeURIComponent(searchValue.trim())}`);
    };

    const handleVersionChange = (version: string) => {
        const newVersion = version
        setVersion(newVersion);
        router.push(`/nomenclatures?limit=${limit}&page=${page}&version=${newVersion}&name=${encodeURIComponent(searchValue.trim())}`);
    }

    const handleVersionEnter = (version: string) => {
        setVersion(version)
    }

    const handleTimeZoneChange = (value: string) => {
        const newTimeZone = value
        setTimezone(newTimeZone)
        router.push(`/nomenclatures?limit=${limit}&page=${page}&version=${version}&name=${encodeURIComponent(searchValue.trim())}&timezone=${newTimeZone}`);
    }
    

    const logOut = () => {
        AuthService.logout();
        router.push('/auth');
    }
    
    const handlePageChange = (page: number, pageSize?: number) => {
        const limit = pageSize || 10;
        router.push(`/nomenclatures?limit=${limit}&page=${page}`);
    };

    return (
        <div>        
            <div className={styles['cont']}>
                <div style={{width: '360px', padding: '16px'}}>
                    {/* name */}
                    <Search
                        placeholder="Поиск по наименованию"
                        allowClear
                        onSearch={handleSearchEnter}
                        onChange={e => handleSearchChange(e.target.value)}
                        value={searchValue}
                        style={{ width: '100%' }}
                    />
                    {/* version */}
                    <Search
                        placeholder="Поиск по версиям"
                        allowClear
                        onSearch={handleVersionEnter}
                        onChange={e => handleVersionChange(e.target.value)}
                        value={version}
                        style={{ width: '100%' }}
                    />
                    {/* status */}
                    <Select
                        placeholder='Выберите статус'
                        onSelect={handleStatusEnter}
                        onChange={e => handleStatusChange(e)}
                        options={[
                            { value: 'null', label: 'Все' },
                            { value: '0', label: 'доступно' },
                            { value: '1', label: 'недоступно меньше часа' },
                            { value: '2', label: 'недоступно больше часа' },
                        ]}
                        style={{ width: '100%' }}
                    />
                    {/* timezone */}
                    <Select placeholder='timezone' onChange={handleTimeZoneChange} style={{ width: '100%' }}>
                        {/* Отображение временных зон в компоненте Select */}
                        {timezonesArray.map(timezone => (
                            <Option key={timezone.value} value={timezone.value}>{timezone.label}</Option>
                        ))}
                    </Select>
                </div>
                <div className={styles['menu-table']}>
                    <div className={styles['menu-table_row']}>
                        <div className={styles['menu-table_item']}>Наименование</div>
                        <div className={styles['menu-table_item']}>Часовой пояс</div>
                        <div className={styles['menu-table_item']}>Последнее время ответа</div>
                        <div className={styles['menu-table_item']}>Версия</div>
                    </div>
                    {data.results.map(el => (
                        <div className={styles['menu-table_row']} key={el.id}>
                            <div className={styles['menu-table_item']}><Link href={`/nomenclatures/${el.id}`} rel="noopener noreferrer" target="_blank">{el.name}</Link></div> 
                            <div className={styles['menu-table_item']}>{el.timezone}</div>
                            <div className={styles['menu-table_item']}>{el.last_answer}</div>
                            <div className={styles['menu-table_item']}>{el.version}</div>
                        </div>
                    ))}
                    <div style={{ display: 'flex', flexDirection: 'row', gap: '24px', alignItems: 'center', justifyContent: 'center', marginTop: '48px' }}>
                        Общее кол-во: {data.count}
                        <Pagination
                            current={parseInt(router.query.page as string) || 1}
                            pageSize={parseInt(router.query.limit as string) || 10}
                            total={data.count}
                            onChange={handlePageChange}
                            showSizeChanger
                            onShowSizeChange={handlePageChange}
                            pageSizeOptions={['10', '25', '50', '100']}
                            style={{ display: 'flex', justifyContent: 'center' }}
                        />
                    </div>
                <button onClick={logOut}>Выход</button>
                </div>
                
            
            </div>
            </div>
    );
}

export const getServerSideProps: GetServerSideProps = async (context) => {

    const { query } = context;
    const limit = parseInt(query.limit as string) || 10;
    const page = parseInt(query.page as string) || 1;
    const search = query.name ? `&name=${encodeURIComponent(query.name as string)}` : '';
    const status = query.status ? `&status=${encodeURIComponent(query.status as string)}` : '';
    const version = query.version ? `&version=${encodeURIComponent(query.version as string)}` : '';
    const timezone = query.timezone ? `&timezone=${encodeURIComponent(query.timezone as string)}` : '';
    const isAuth = await AuthService.isAuthenticated(context.req);

    if (!isAuth) {
        return {
            redirect: {
                destination: '/auth',
                permanent: false,
            },
        };
    }


    try {
        const res = await fetch(`${API_URL}/api/nomenclatures/?limit=${limit}&page=${page}${search}${status}${version}${timezone}`);
        if (!res.ok) {
            throw new Error('Failed to fetch data');
        }
        const data = await res.json();
        return {
            props:{
                data: data
            }
        }
    } catch (error: Error | any) {
        console.log('Failed to fetch:', error)
        return {
            props: {
                data: null,
                error: error.message
            }
        }
    }
}
