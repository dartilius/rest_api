'use client'

import {useParams, useRouter} from "next/navigation";
import {Button} from "@mui/material";



function Page() {

    const router = useRouter()
    const { id } = useParams();

    const handleBack = () => {
        router.back()
    }
    return (
        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
            <Button onClick={handleBack} variant='contained' color='secondary' style={{maxWidth: '120px'}}>Назад</Button>
            Редактирование
        </div>
    );
}

export default Page;