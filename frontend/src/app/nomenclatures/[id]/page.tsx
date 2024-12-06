"use client";

import { useFetchNomenclatureById } from "@/hooks/useFetchNomenclatures";
import useIdFromParams from "@/hooks/useIdFromParam";

export default function NomenclaturePage() {
    const token = localStorage.getItem("accessToken");
    const id = useIdFromParams()
    const { fetchData, nomenclature } = useFetchNomenclatureById({ id, token })

    console.log(nomenclature);

    return (
        <div style={{ fontWeight: 900 }}>NomenclaturePage</div>
    );
}