import { API_URL } from '@/config/api.config'
import { client } from '@/services/httpClient'
import { IBgOrderDetail, IDataBgResponse } from '@/types/orderTypes'
import { getServerAccessToken, getClientAccessToken } from '@/utils'

const isSSR = typeof window === 'undefined'
console.log('isSsr', isSSR)

export async function getDataBg(queryParams: {
	page: number
	limit: number
	name: string
	client: string
	status: string
	created_after: string
	created_before: string
	order_type: string
	since_after: string
	since_before: string
	until_after: string
	until_before: string
}): Promise<IDataBgResponse> {
	let token
	if (isSSR) {
		// Для SSR получаем токен с сервера
		token = await getServerAccessToken()
		console.log('token isSsr', token)
	} else {
		// Для клиента получаем токен с клиента
		token = getClientAccessToken()
		console.log('token !isSsr', token)
	}

	const stringifiedQueryParams = {
		...queryParams,
		page: queryParams.page.toString(),
		limit: queryParams.limit.toString(),
		name: queryParams.name.toString(),
		client: queryParams.client.toString(),
		order_type: queryParams.order_type.toString(),
		created_after: queryParams.created_after.toString(),
		created_before: queryParams.created_before.toString(),
	}

	const url = `${API_URL}bgorders`

	const res = await client.get<IDataBgResponse>(url, {
		params: stringifiedQueryParams,
		headers: {
			Authorization: `access_token ${token}`,
		},
	})
	console.log(res)

	return res
}

export async function getBgOrderDetail(id: string): Promise<IBgOrderDetail> {
	try {
		const token = await getServerAccessToken()
		const url = `${API_URL}bgorders/${id}`

		const res = await client.get<IBgOrderDetail>(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
		})

		if (!res) {
			throw new Error('Order not found')
		}

		return res
	} catch (error) {
		console.error('Error fetching order detail:', error)
		throw error
	}
}
export interface ICancelResponse {
	success: boolean
	message?: string
	error?: string
}

export async function cancelBgOrder(id: string): Promise<ICancelResponse> {
	try {
		const token = getClientAccessToken()
		const url = `${API_URL}bgorders/${id}/cancel/`

		const res = await client.delete<ICancelResponse>(url, {
			headers: {
				Authorization: `access_token ${token}`,
				'Content-Type': 'application/json',
			},
		})
		console.log(res)

		return res
	} catch (error) {
		console.error('Cancel error:', error)
		throw new Error('Ошибка отмены заказа')
	}
}
