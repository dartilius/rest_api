'use client';

import { IconButton } from "@mui/material";
import Image from "next/image";
import {useState} from "react";
import {deleteNomenclatures} from "@/services/NomenclaturesService";
import {useRouter} from "next/navigation";
import {gifDelete, gifEdit, staticDelete, staticEdit} from "@/styles";
import {nomenclaturesService} from "@/app/nomenclatures/api";

type NomenclatureActionsProps = {
    id: string;
};

export function NomenclatureActions({ id }: NomenclatureActionsProps) {

    const [imageEditSrc, setImageEditSrc] = useState<typeof staticEdit | typeof gifEdit>(staticEdit);
    const [imageDeleteSrc, setImageDeleteSrc] = useState<typeof staticDelete | typeof gifDelete>(staticDelete);
    const router = useRouter()

    async function handleDelete() {
        try {
            console.log("Delete:", id);
            const res = await nomenclaturesService.deleteNomenclature(id);
            console.log(res);

            if (res === 204) {
                router.refresh(); // обновить страницу после успешного удаления
            } else {
                console.error('Error during deletion:', res);
                // Можно здесь добавить отображение уведомления для пользователя
            }
        } catch (error) {
            console.error("Error deleting nomenclature:", error);
            // Можно здесь обработать ошибки, например, через UI уведомление
        }
    }

        async function handleEdit() {
        router.push(`/nomenclatures/edit/${id}`);
    }

    return (
        <div>
            <IconButton onClick={handleEdit} style={{background: 'none'}}>
                <Image
                    src={imageEditSrc}
                    alt='edit'
                    width={24}
                    height={24}
                    style={{
                        background: 'none',
                        transition: 'opacity 0.3s ease',
                    }}
                    onMouseEnter={() => setImageEditSrc(gifEdit)}
                    onMouseLeave={() => setImageEditSrc(staticEdit)}
                />
            </IconButton>
            <IconButton onClick={handleDelete}>
                <Image
                    src={imageDeleteSrc}
                    alt='edit'
                    width={24}
                    height={24}
                    style={{
                        background: 'none',
                        transition: 'opacity 0.3s ease',
                    }}
                    onMouseEnter={() => setImageDeleteSrc(gifDelete)}
                    onMouseLeave={() => setImageDeleteSrc(staticDelete)}
                />
            </IconButton>
        </div>
    );
};
