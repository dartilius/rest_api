import {API_URL} from "@/config/api.config";
import {IFIleResponse, IFilesListResponse} from "@/interfaces/Files.Interface";
import {getAccessToken} from "@/services/accessToken";
import {cookies} from "next/headers";
import ApiRequest from "@/services/ApiRequest";

class FilesService extends ApiRequest{
    constructor() {
        super('files', API_URL);
    }

    async getAll(queryParams?: any): Promise<IFilesListResponse> {
        return super.getAll(queryParams)
    }

    async getById(id: string): Promise<IFIleResponse[]> {
        return super.getById(id);
    }
}

export default new FilesService()