import React from 'react';
import {fetchFilesList, fetchFilesResponse} from "@/services/FilesService";

type FiltersWrapperProps = {
    name: string;
    currentPage: number
    limit: number
    file_type: string;
    tags: string;
}

export async function List(props: FiltersWrapperProps) {
    const {tags,file_type,name,currentPage,limit} = props

    const listFiles = await fetchFilesList({page: currentPage,limit})

    // console.log(listFiles)

    return (
        <div></div>
    );
}