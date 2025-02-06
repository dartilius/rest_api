import { INomenclatureByIdResponse } from '@/interfaces/Nomenclatures.interface'
import { convertStatus } from '@/types/checkStatus'
import { Skeleton } from '@mui/material'
import React from 'react'
import '../nomenclature.scss'
import '@/styles/_vars.scss'


interface MainInfoProps {
    main_info: INomenclatureByIdResponse['main_info']; // main_info соответствует типу main_info из INomenclatureByIdResponse
}

const MainInfo = (props: MainInfoProps) => {
    const { main_info } = props
    return (
        <div className="main-info">
            <div style={{ color: '#f55f5f' }}>
                {
                    main_info ?
                        main_info.name :
                        <Skeleton
                            animation="pulse"
                            variant="text"
                            width='auto'
                            sx={{ bgcolor: '#f99f9f' }}
                        />
                }
            </div>
            <div className="main-info__list-answer">
                Время последнего ответа:
                <div className="main-info__list-answer__item">
                    {
                        main_info ?
                            main_info.last_answer :
                            <Skeleton
                                animation="pulse"
                                variant="text"
                                width={240}
                                sx={{ bgcolor: '#f99f9f' }}
                            />
                    }
                </div>
            </div>
            <div className="main-info__description">
                Описание
                <div className="main-info__description__item">
                    {
                        main_info ?
                            main_info.description :
                            <Skeleton
                                animation="pulse"
                                variant="rounded"
                                sx={{ bgcolor: '#f99f9f' }}
                            />
                    }
                </div>
            </div>
            <div className="main-info__timezone">
                Часовой пояс:
                <div className="main-info__timezone__item">
                    {
                        main_info ?
                            main_info.timezone :
                            <Skeleton
                                animation="pulse"
                                variant="text"
                                width={240}
                                sx={{ bgcolor: '#f99f9f' }}
                            />
                    }
                </div>
            </div>
            <div className="main-info__owner">
                Владелец:
                <div className="main-info__owner__item">
                    {
                        main_info ?
                            main_info.owner.full_name :
                            <Skeleton
                                animation="pulse"
                                variant="text"
                                width={240}
                                sx={{ bgcolor: '#f99f9f' }}
                            />
                    }
                </div>
            </div>
            <div className="main-info__status">
                Статус:
                <div className="main-info__status__item">
                    {
                        main_info ?
                            convertStatus(main_info.status) :
                            <Skeleton
                                animation="pulse"
                                variant="text"
                                width={240}
                                sx={{ bgcolor: '#f99f9f' }}
                            />
                    }
                </div>
            </div>
            <div className="main-info__version">
                Версия ПО:
                <div className="main-info__version__item">
                    {
                        main_info ?
                            main_info.version :
                            <Skeleton
                                animation="pulse"
                                variant="text"
                                width={240}
                                sx={{ bgcolor: '#f99f9f' }}
                            />
                    }
                </div>
            </div>
            <div className="main-info__created">
                Создана:
                <div className="main-info__created__item">
                    {
                        main_info ?
                            main_info.created :
                            <Skeleton
                                animation="pulse"
                                variant="text"
                                width={240}
                                sx={{ bgcolor: '#f99f9f' }}
                            />
                    }
                </div>
            </div>
        </div>
    )
}

export default MainInfo