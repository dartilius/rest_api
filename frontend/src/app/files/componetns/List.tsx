import React from 'react';
import {FilesDataList} from "@/services/FilesService";
import {Item} from "@/app/files/componetns/Item";
import {Pagination} from "@/app/files/componetns/Pagination";

type FiltersWrapperProps = {
    data: FilesDataList[]
    count: number;
    limit: number;
    currentPage: number;
}

export async function List(props: FiltersWrapperProps) {
    const {data, count, limit, currentPage} = props
    const totalPages = Math.ceil(count / limit);
    console.log(data)
    return (
        <div>
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',  // 4 колонки по умолчанию
                gap: '16px',
                paddingLeft: '24px',
                // '@media (max-width: 768px)': {
                //     gridTemplateColumns: 'repeat(1, 1fr)',  // 2 колонки на мобильных устройствах
                // }
            }}>
                {data?.map((item) => (
                    <div key={item.id}>
                        <Item item={item} />
                    </div>
                ))}
            </div>
            <Pagination currentPage={currentPage} totalPages={totalPages} />
        </div>
    );
}