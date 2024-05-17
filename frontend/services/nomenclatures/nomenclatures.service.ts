import { API_URL } from "@/config/api.config"
import { NomenclatureListResponseInterface } from "@/shared/interface/Nomenclature.interface";

export const NomenclaturesService = {

    async get(): Promise<NomenclatureListResponseInterface>{
        const response = await fetch(`${API_URL}/api/nomenclatures/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Не удалось получить номенклатуру');
        }
    },

    async create(updatedData: any, token: string | undefined) {
        const response = await fetch(`${API_URL}/api/nomenclatures/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(updatedData)
        });

        if (response.status === 201 || response.status === 200) {
            return response;
        } else {
            throw new Error('Не удалось создать номенклатуру');
        }
    },

    async delete(token: string | undefined, id: string | string[] | undefined) {
        const response = await fetch(`${API_URL}/api/nomenclatures/${id}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 204 || response.status === 200) {
            return response;
        } else {
            throw new Error('Не удалось удалить номенклатуру');
        }
    }
}
