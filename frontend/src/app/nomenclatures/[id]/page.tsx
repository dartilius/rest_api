"use client";

import { useFetchNomenclatureById } from "@/hooks/useFetchNomenclatures";
import useIdFromParams from "@/hooks/useIdFromParam";
import './nomenclature.scss'
import nomenclature from './test.json'
import { convertStatus } from "@/types/checkStatus";

export default function NomenclaturePage() {
    // const token = localStorage.getItem("accessToken");
    // const id = useIdFromParams()
    // const { fetchData, nomenclature } = useFetchNomenclatureById({ id, token })

    console.log(nomenclature);
    if (!nomenclature) return;

    return (
        <div className="nomenclature">
            <div className="main-info">
                <div>
                    {nomenclature.main_info.name}
                </div>
                <div className="main-info__list-answer">
                    Время последнего ответа:
                    <div className="main-info__list-answer__item">
                        {nomenclature.main_info.last_answer}
                    </div>
                </div>
                <div className="main-info__description">
                    Описание
                    <div className="main-info__description__item">{nomenclature.main_info.description}</div>
                </div>
                <div className="main-info__timezone">
                    Часовой пояс:
                    <div className="main-info__timezone__item">
                        {nomenclature.main_info.timezone}
                    </div>
                </div>
                <div className="main-info__owner">
                    Владелец:
                    <div className="main-info__owner__item">{nomenclature.main_info.owner}</div>
                </div>
                <div className="main-info__status">
                    Статус:
                    <div className="main-info__status__item">{convertStatus(nomenclature.main_info.status)}</div>
                </div>
                <div className="main-info__version">
                    Версия ПО:
                    <div className="main-info__version__item">{nomenclature.main_info.version}</div>
                </div>
                <div className="main-info__created">
                    Создана:
                    <div className="main-info__created__item">{nomenclature.main_info.created}</div>
                </div>
            </div>
            <div className="settings">
                <div>Настройки</div>
            </div>

            <div className="hwinfo">

                <div className="hwinfo__main">
                    <div style={{ color: '#f55f5f' }}>HwInfo</div>
                    <div className="hwinfo__main__model">
                        Модель:
                        <div className="hwinfo__main__model__item">{nomenclature.hw_info.model}</div>
                    </div>
                    <div className="hwinfo__main__revision">
                        Ревизия:
                        <div className="hwinfo__main__revision__item">{nomenclature.hw_info.revision}</div>
                    </div>
                    <div className="hwinfo__main__serial-number">
                        Серийный номер:
                        <div className="hwinfo__main__serial-number__item">{nomenclature.hw_info.serial_number}</div>
                    </div>
                </div>
                <div className="hwinfo__audio-devices">
                    Аудио устройства
                    <div className="hwinfo__audio-devices__item">{nomenclature.hw_info.audiodevices.map((item) => item.name).join(', ')}</div>
                </div>
                <div className="hwinfo__interfaces">
                    <div style={{ color: '#f55f5f' }}>Интерфейсы</div>
                    <div className="hwinfo__interfaces__list">
                        {nomenclature.hw_info.interfaces.map((iface, index) => (
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
                </div>
                <div className="hwinfo__sd-card">
                    <div style={{ color: '#f55f5f' }}>Sd card</div>
                    <div className="hwinfo__sd-card__title">
                        Название:
                        <div className="hwinfo__sd-card__item">{nomenclature.hw_info.sd_card_data.name}</div>
                    </div>
                    <div className="hwinfo__sd-card__title">
                        id:
                        <div className="hwinfo__sd-card__item">{nomenclature.hw_info.sd_card_data.manf_id}</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
