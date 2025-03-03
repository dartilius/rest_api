//TODO: Разбить на компоненты, чтобы юзать SSR
'use client'
import useIdFromParams from '@/hooks/useIdFromParam';
import './nomenclature.scss'
import { useFetchNomenclatureById } from '@/hooks/useFetchNomenclatures';
import MainInfo from './components/MainInfo';
import Settings from './components/Settings';
import {useRouter} from "next/navigation";
import {Button} from "@mui/material";


export default function NomenclaturePage() {
    const id = useIdFromParams()
    // console.log(id);
    
    const { error, isError, refetch, isLoading, nomenclature } = useFetchNomenclatureById(id)
    const router = useRouter();
    const handleBack = () => {
        router.back()
    }

    return (
        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            <Button onClick={handleBack} variant='contained' color='secondary' style={{maxWidth: '120px'}}>Назад</Button>
            <div className="nomenclature">

                <MainInfo main_info={nomenclature?.main_info} />
                <Settings settings={nomenclature?.settings} />

                <div className="hwinfo">
                    <div style={{ color: '#f55f5f' }}>HwInfo</div>
                    {nomenclature?.hw_info ? (
                        <><div className="hwinfo__main">

                            <div className="hwinfo__main__model">
                                Модель:
                                <div className="hwinfo__main__model__item">{nomenclature?.hw_info.model}</div>
                            </div>
                            <div className="hwinfo__main__revision">
                                Ревизия:
                                <div className="hwinfo__main__revision__item">{nomenclature?.hw_info.revision}</div>
                            </div>
                            <div className="hwinfo__main__serial-number">
                                Серийный номер:
                                <div className="hwinfo__main__serial-number__item">{nomenclature?.hw_info.serial_number}</div>
                            </div>
                        </div><div className="hwinfo__audio-devices">
                                Аудио устройства
                                <div className="hwinfo__audio-devices__item">{nomenclature?.hw_info.audiodevices.map((item: any) => item.name).join(', ')}</div>
                            </div><div className="hwinfo__interfaces">
                                <div style={{ color: '#f55f5f' }}>Интерфейсы</div>
                                <div className="hwinfo__interfaces__list">
                                    {nomenclature?.hw_info.interfaces.map((iface: any, index: any) => (
                                        <div key={index}>
                                            <div className="hwinfo__interfaces__title">
                                                Интерфейс:
                                                <div className="hwinfo__interfaces__item">
                                                    {iface.iface || "Не указано"}
                                                </div>
                                            </div>
                                            <div className="hwinfo__interfaces__title">
                                                IP:
                                                <div className="hwinfo__interfaces__item">
                                                    {iface.ip || "Не указано"}
                                                </div>
                                            </div>
                                            <div className="hwinfo__interfaces__title">
                                                MAC:
                                                <div className="hwinfo__interfaces__item">
                                                    {iface.mac || "Не указано"}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div><div className="hwinfo__sd-card">
                                <div style={{ color: '#f55f5f' }}>Sd card</div>
                                <div className="hwinfo__sd-card__title">
                                    Название:
                                    <div className="hwinfo__sd-card__item">{nomenclature?.hw_info.sd_card_data.name}</div>
                                </div>
                                <div className="hwinfo__sd-card__title">
                                    id:
                                    <div className="hwinfo__sd-card__item">{nomenclature?.hw_info.sd_card_data.manf_id}</div>
                                </div>
                            </div></>

                    ) : (<div>Нету</div>)}
                </div>
                <div className="knopochki" style={{ color: '#f55f5f' }}>Кнопочки</div>
            </div>
        </div>
    );
}