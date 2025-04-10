'use client'
import React from 'react';
import { IconButton, Tooltip, Zoom } from '@mui/material';
import Image from "next/image";
import { staticDelete, staticEdit, staticView } from "@/styles";

type Props = {
    handleDelete: (id: string) => void;
    toggleCollapse: (id: string) => void;
    handleEdit: (id: string) => void;
    id: string;
}

function IconActions(props: Props) {
    const { handleDelete, id, toggleCollapse, handleEdit } = props;

    return (
        <div style={{
            display: 'flex',
            gap: '8px',
            alignItems: 'center',
            justifyContent: 'flex-end',
            paddingRight: '8px'
        }}>
            <Tooltip
                title="Редактировать"
                TransitionComponent={Zoom}
                enterDelay={300}
            >
                <IconButton aria-label="Редактировать файл" onClick={() => handleEdit ? handleEdit(id) : console.log(2)}>
                    <Image
                        src={staticEdit}
                        alt="edit"
                        width={24}
                        height={24}
                        style={{ filter: 'opacity(0.7)' }}
                    />
                </IconButton>
            </Tooltip>

            <Tooltip
                title="Удалить"
                TransitionComponent={Zoom}
                enterDelay={300}
            >
                <IconButton
                    onClick={() => handleDelete ? handleDelete(id) : console.log(1)}
                    aria-label="Удалить файл"
                >
                    <Image
                        src={staticDelete}
                        alt="delete"
                        width={24}
                        height={24}
                        style={{ filter: 'opacity(0.7)' }}
                    />
                </IconButton>
            </Tooltip>

            <Tooltip
                title={"Превью файла"}
                TransitionComponent={Zoom}
                enterDelay={300}
            >
                <IconButton
                    onClick={() => toggleCollapse(id)}
                    aria-label="Превью файла"
                    sx={{
                        transform:'rotate(180deg)',
                        transition: 'transform 0.3s ease-in-out',
                    }}
                >
                    <Image
                        src={staticView}
                        alt="view"
                        width={24}
                        height={24}
                        style={{ filter: 'opacity(0.7)' }}
                    />
                </IconButton>
            </Tooltip>
        </div>
    );
}

export default IconActions;