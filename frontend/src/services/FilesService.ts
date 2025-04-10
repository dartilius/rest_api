import { API_URL } from '@/config/api.config'
import { getClientAccessToken, getServerAccessToken } from '@/utils'
import { getAccessToken } from '@/services/accessToken'
import {IFileDetailResponse, IFilesListResponse, ITagResponse, ITagsListResponse} from '@/types/fileTypes'
import { client } from '@/services/httpClient'



const getToken = async () => {
	const isSSR = typeof window === 'undefined'
	let token
	if (isSSR) {
		token = await getServerAccessToken()
	} else {
		token = getClientAccessToken()
	}

	return token
}

export async function getFilesList(queryParams: {
	page: number
	limit: number
	name: string
	file_type: string
	tags: string[]
}): Promise<IFilesListResponse> {
	const token = await getToken();

	const stringifiedQueryParams: Record<string, any> = {
		page: queryParams.page.toString(),
		limit: queryParams.limit.toString(),
		name: queryParams.name.toString(),
		file_type: queryParams.file_type.toString(),
	};

	// Добавляем tags только если массив не пуст
	if (queryParams.tags.length > 0) {
		stringifiedQueryParams.tags = queryParams.tags;
	}

	const url = `${API_URL}files`;

	console.log('stringifiedQueryParams', stringifiedQueryParams);

	return await client.get<IFilesListResponse>(url, {
		params: stringifiedQueryParams,
		headers: {
			Authorization: `access_token ${token}`,
		},
	});
}



export async function getFileDetail(id: string): Promise<IFileDetailResponse> {
	const token = await getToken()
	try {
		const response = await fetch(`${API_URL}files/${id}`, {
			headers: {
				'Content-Type': 'application/json',
				Accept: 'application/json',
				Authorization: `access_token ${token}`,
			},
			method: 'GET',
		})

		if (!response.ok) {
			throw new Error(
				`Ошибка загрузки файлов: статус ${response.status}, текст: ${response.statusText}`,
			)
		}

		return (await response.json()) as IFileDetailResponse
	} catch (error) {
		console.error('Ошибка при запросе файлов:', error)
		throw error
	}
}

type SendFile = {
	type: number
	source: string
	tags: ITagResponse[]
}

type SendFileResponse =
	| {
			id: string
			length: string
			size: number
			type: string
			tags: string[]
			url: string
			name: string
			owner: {
				full_name: string
			}
			hash: string
			created: string
	  }

type ErrorResponse = {
	source: string[]
}

export async function sendFile(body: SendFile): Promise<SendFileResponse> {
	const token = await getToken()

	try {
		const response = await fetch(`${API_URL}files/`, {
			headers: {
				'Content-Type': 'application/json',
				Accept: 'application/json',
				Authorization: `access_token ${token}`,
			},
			method: 'POST',
			body: JSON.stringify(body),
		})

		if (!response.ok) {
			throw new Error(await response.text())
		}

		return (await response.json()) as SendFileResponse
	} catch (error: any) {
		console.error('Ошибка при создании файла:', error)
		throw error
	}
}

export async function deleteFile(id: string): Promise<any> {
	const token = await getToken()
	try {
		const response = await fetch(`${API_URL}files/${id}/`, {
			headers: {
				'Content-Type': 'application/json',
				Accept: 'application/json',
				Authorization: `access_token ${token}`,
			},
			method: 'DELETE',
		})

		if (!response.ok) {
			let errorMessage = `Ошибка при удалении файла: статус ${response.status}`

			try {
				const errorData: ErrorResponse = await response.json()
				if (errorData.source && errorData.source.length > 0) {
					errorMessage += `, источник ошибки: ${errorData.source.join(', ')}`
				}
			} catch (jsonError) {
				errorMessage += ', не удалось распарсить ошибку'
			}

			throw new Error(errorMessage)
		}
		return response
	} catch (error: any) {
		console.error('Ошибка при удалении файла:', error)
		throw error
	}
}

export async function addTags(id: string, tags: string[]) {
	const token = await getToken()

	const url = `${API_URL}files/${id}/add_tags/`

	return await fetch(url, {
		method: 'POST',
		headers: {
			Authorization: `access_token ${token}`,
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ tags }),
	})
}

export async function removeTags(id: string, tags: string[]) {
	const token = await getToken()

	const url = `${API_URL}files/${id}/remove_tags/`

	return await fetch(url, {
		method: 'POST',
		headers: {
			Authorization: `access_token ${token}`,
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ tags }),
	})
}

export async function getTagList(page: number): Promise<ITagsListResponse> {
	const token = await getToken()

	const url = `${API_URL}tags/?page=${page}`

	const response = await fetch(url, {
		headers: {
			Authorization: `access_token ${token}`,
		},
	})

	if (!response.ok) {
		throw new Error(`Failed to fetch tags: ${response.statusText}`)
	}

    return await response.json() as ITagsListResponse
}

export async function createTag(name: string): Promise<ITagResponse> {
	const token = await getToken()
	const url = `${API_URL}tags/`
	const res =  await fetch(url, {
		method: 'POST',
		headers: {
			Authorization: `access_token ${token}`,
			'Content-Type': 'application/json',
		},
		body: JSON.stringify({ name }),
	})

	if (!res.ok) {
		throw new Error(`Failed to create tags: ${res.statusText}`)
	}

	return await res.json() as ITagResponse
}