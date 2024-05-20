'use client'

import { NomenclaturesService } from "@/services/nomenclatures/nomenclatures.service";
import { NomenclatureInterface } from "@/shared/interface/nomenclature.interface";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

export default function Nomenclature() {
    // const { id } = params || { id: '' }; // Ensure id is initialized to a default value
    const router = useRouter();
    const { id } = router.query;

    const [nomenclatures, setNomenclatures] = useState<NomenclatureInterface>();

    useEffect(() => {
        console.log(id);
        
        const fetchNomenclatures = async () => {
            try {
                if (id) { // Check if id is truthy
                    const data: NomenclatureInterface = await NomenclaturesService.getById(id);
                    setNomenclatures(data);
                }
            } catch (error) {
                console.error('Fetch error:', error);
            }
        };
        fetchNomenclatures();
    }, [id]);

    // if (!id) { // Check if id is falsy
    //     return <div>Loading...</div>;
    // }

    return (
        <div>
            <h1>{nomenclatures?.name}</h1>
        </div>
    );
}
