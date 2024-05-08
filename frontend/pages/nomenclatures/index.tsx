import { API_URL } from '@/config/api.config';
import { GetServerSideProps } from 'next';
import styles from './Nomenclatures.module.scss';
import Custom500 from '../500';
import { Pagination } from 'antd/lib';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import { NomenclatureListResponseInterface } from '@/shared/interface/nomenclature.interface';
import { AuthService } from '@/services/auth/auth.service';

interface INomenclaturesProps {
    data: NomenclatureListResponseInterface | null
    error?: string
}

type Status = 0 | 1 | 2;

// 10 25 50 100

export default function Nomenclatures({data, error}: INomenclaturesProps) {
    
    const router = useRouter()
    const [limit, setLimit] = useState(router.query.limit || 10)
    const [page, setPage] = useState(router.query.page || 1)

    useEffect(() => {
        if (router.isReady) {
            setLimit(parseInt(router.query.limit as string) || 10);
            setPage(parseInt(router.query.page as string) || 1);
        }
    }, [router.isReady, router.query.limit, router.query.page]);
    
    if (error || !data) {
        return <Custom500 />
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
        <>
            <div className={styles['menu-table']}>
                <div className={styles['menu-table_row']}>
                    <div className={styles['menu-table_item']}>Наименование</div>
                    <div className={styles['menu-table_item']}>Часовой пояс</div>
                    <div className={styles['menu-table_item']}>Последнее время ответа</div>
                    <div className={styles['menu-table_item']}>Версия</div>
                </div>
                {data.results.map(el => (
                    <div className={styles['menu-table_row']} key={el.id} onClick={() => router.push(`/nomenclatures/${el.id}`)}>
                        <div className={styles['menu-table_item']}>{el.name}</div>
                        <div className={styles['menu-table_item']}>{el.timezone}</div>
                        <div className={styles['menu-table_item']}>{el.last_answer}</div>
                        <div className={styles['menu-table_item']}>{el.version}</div>
                    </div>
                ))}
            </div>
            <div style={{ display: 'flex', flexDirection: 'row', gap: '24px', alignItems: 'center', justifyContent: 'center' }}>
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
        </>
    );
}

export const getServerSideProps: GetServerSideProps = async (context) => {

    const { query } = context;
    const limit = parseInt(query.limit as string) || 10;
    const page = parseInt(query.page as string) || 1;
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
        const res = await fetch(`${API_URL}/api/nomenclatures/?limit=${limit}&page=${page}`);
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
