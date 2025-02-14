
import {IFilesResult} from "@/interfaces/Files.Interface";

export default function FilesList({ files }: { files: IFilesResult[] }) {
    return (
        <ul>
            {files?.map((file) => (
                <li key={file.id}>{file.name}</li>
            ))}
        </ul>
    );
}