import { fetchFilesById } from "@/services/FilesService";
import Image from "next/image";

type FileResponse = {
    id: string;
    length: string;
    size: number;
    type: string;
    source: string;
    name: string;
    tags: Array<{ id: string; name: string }>;
    url: string;
};

async function getFileById(id: string): Promise<FileResponse | string | null> {
    try {
        return await fetchFilesById({ id }) || '';
    } catch (error) {
        console.error("Ошибка загрузки файла:", error);
        return null;
    }
}

export default async function Page({ params }: { params: { id: string } }) {
    const fileData = await getFileById(params.id);

    if (!fileData) {
        return <p>Данные не найдены.</p>;
    }

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {typeof fileData !== 'string' ? (
                <div>
                    {fileData.type === "music" && <audio controls src={fileData.url} style={{ width: "100%" }} />}
                    {fileData.type === "image" && (
                        <Image src={fileData.url} width={200} height={240} alt={fileData.name} />
                    )}
                </div>
            ) : (
                <div>{fileData}</div>
            )}

        </div>
    );
}
