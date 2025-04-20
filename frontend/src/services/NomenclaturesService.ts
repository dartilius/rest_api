import { API_URL } from '@/config/api.config'
import { getToken } from '@/utils'
import {
	ICreateNomenclature,
	INomenclatureResponse,
	INomenclaturesListResponse,
	NomenclaturesListProps,
} from '@/types/nomeclaturesType'
import { client } from '@/services/httpClient'

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
	console.log(url)

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

export async function getNomenclatureList(queryParams: {
	searchParams?: Promise<NomenclaturesListProps>
}): Promise<INomenclaturesListResponse> {
	const token = await getToken()
	const url = `${API_URL}nomenclatures`
	const resolvedParams = (await queryParams.searchParams) || {}
	const strQueryParams = {
		...resolvedParams,
		page: Number(resolvedParams.page || 1),
		limit: Number(resolvedParams.limit || 10),
	}

	try {
		return await client.get<INomenclaturesListResponse>(url, {
			params: strQueryParams,
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