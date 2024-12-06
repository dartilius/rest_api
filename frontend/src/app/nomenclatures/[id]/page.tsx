"use client";

import { useFetchNomenclatureById } from "@/hooks/useFetchNomenclatures";
import useIdFromParams from "@/hooks/useIdFromParam";
import './nomenclature.scss'

export default function NomenclaturePage() {
    const token = localStorage.getItem("accessToken");
    const id = useIdFromParams()
    const { fetchData, nomenclature } = useFetchNomenclatureById({ id, token })

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
                <div>
                    <div>
                        Описание:
                        <div>{nomenclature.main_info.description}</div>
                    </div>
                </div>
            </div>
            <div className="settings">settings</div>
            <div className="hwinfo">hwinfo</div>
        </div>
    );
}