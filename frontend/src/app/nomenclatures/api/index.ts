import { API_URL } from "@/config/api.config"
import { client } from "@/services/httpClient"
import { ICreateNomenclature, INomenclatureResponse, INomenclaturesListResponse, INomenclatureStatisticsResponse, INomenclatureStatusHistoryResponse, IUpdateNomenclature, NomenclaturesListProps } from "@/types/nomeclaturesType"
import { getToken } from "@/utils"

export async function getNomenclatureList(queryParams: NomenclaturesListProps): Promise<INomenclaturesListResponse> {
	const token = await getToken()
	const url = `${API_URL}nomenclatures`
    const stringifiedQueryParams: Record<string, any> = {
        page: queryParams.page?.toString(),
        limit: queryParams.limit?.toString(),
        name: queryParams.name?.toString(),
        status: queryParams.status?.toString(),
        timezone: queryParams.timezone?.toString(),
        version: queryParams.version?.toString()

    }

	try {
		return await client.get<INomenclaturesListResponse>(url, {
			params: stringifiedQueryParams,
			headers: {
				Authorization: `access_token ${token}`,
			},
		})
	} catch (error) {
		console.error('Ошибка при запросе номенклатуры:', error)
		throw error
	}
}

export async function deleteNomenclatures(id: string): Promise<number> {
	const token = await getToken()
	const url = `${API_URL}nomenclatures/${id}/`

	try {
		return await client.delete<number>(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
		})
	} catch (error) {
		console.error('Error delete nomenclatures:', error)
		throw new Error('Failed delete nomenclatures')
	}
}

interface IActionNomenclatureResponse {
	status?: number
	message?: string
	detail?: string
}

export async function resendOrders(id: string): Promise<IActionNomenclatureResponse> {
	const token = await getToken()
	const url = `${API_URL}nomenclatures/${id}/resend_orders/`
	try {
		const resend: IActionNomenclatureResponse = await client.post(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
		})

		console.log(resend.message)

		return {
			status: resend.status,
			message: resend.message || `Статус: ${resend.status}`,
			detail: resend.detail,
		}
	} catch (error) {
		console.error('Ошибка при переотправке заказов:', error)
		throw error
	}
}

export async function sendActions(
	id: string,
	type: string,
	parameters?: string,
): Promise<IActionNomenclatureResponse> {
	const token = await getToken()
	const url = `${API_URL}nomenclatures/${id}/actions/`

	try {
		const resend: IActionNomenclatureResponse = await client.post(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
			body: { task: type, parameters: parameters },
		})

		return {
			status: resend.status,
			message: resend.message || `Статус: ${resend.status}`,
			detail: resend.detail,
		}
	} catch (error) {
		console.error('Ошибка при переотправке заказов:', error)
		throw error
	}
}

export async function getNomenclatureDetail(id: string): Promise<INomenclatureResponse> {
	const token = await getToken()
	const url = `${API_URL}nomenclatures/${id}`
	try {
		return await client.get<INomenclatureResponse>(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
		})
	} catch (error) {
		console.error('Ошибка при запросе номенклатуры:', error)
		throw error
	}
}

export async function createNomenclature(body: ICreateNomenclature): Promise<INomenclatureResponse> {
	const token = await getToken()
	const url = `${API_URL}nomenclatures/`

	try {
		return await client.post<INomenclatureResponse>(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
			body: body
		})
	} catch (error) {
		console.error('Ошибка при запросе номенклатуры:', error)
		throw error
	}
}

export async function updateNomenclature(id: string, body: IUpdateNomenclature): Promise<INomenclatureResponse> {
	const token = await getToken()
	const url = `${API_URL}nomenclatures/${id}/`

	try {
		return await client.patch<INomenclatureResponse>(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
			body: body,
		})
	} catch (error) {
		console.error('Ошибка при обновлении номенклатуры:', error)
		throw error
	}
}

export async function getNomenclatureStatistics(id: string): Promise<INomenclatureStatusHistoryResponse[]> {
	const token = await getToken()
	const url = `${API_URL}nomenclatures/${id}/status_history/`

	try {
		return await client.get<INomenclatureStatusHistoryResponse[]>(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
		})
	} catch (error) {
		console.error('Ошибка при запросе статистики номенклатуры:', error)
		throw error
	}
}	

export async function getNomenclaturePlayedStatistics(id: string, page: number, type: string): Promise<INomenclatureStatisticsResponse> {
	const token = await getToken()
	//тут лимит по приколу установлен 100, надо будет поменять
	const url = `${API_URL}nomenclatures/${id}/${type}_stat/?page=${page}&limit=100`

	try {
		return await client.get<INomenclatureStatisticsResponse>(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
		})
	} catch (error) {
		console.error('Ошибка при запросе статистики номенклатуры:', error)
		throw error
	}
}