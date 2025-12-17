import { API_URL } from '@/config/api.config'
import {getToken} from '@/utils'
import {
    ICreateFile,
	ICreateFileResponse,
	IFileDetailResponse,
	IFilesListResponse,
	ITagResponse,
	ITagsListResponse,
} from '@/types/fileTypes'
import { client } from '@/services/httpClient'

export async function getFilesList(queryParams: {
	page: number
	limit: number
	name: string
	file_type: string
	tags: string[]
}): Promise<IFilesListResponse> {
	const token = await getToken()

	const stringifiedQueryParams: Record<string, any> = {
		page: queryParams.page.toString(),
		limit: queryParams.limit.toString(),
		name: queryParams.name.toString(),
		file_type: queryParams.file_type.toString(),
	}

	if (queryParams.tags.length > 0) {
		stringifiedQueryParams.tags = queryParams.tags
	}

	const url = `${API_URL}files`

	return await client.get<IFilesListResponse>(url, {
		params: stringifiedQueryParams,
		headers: {
			Authorization: `access_token ${token}`,
		},
	})
}

export async function getFileDetail(id: string): Promise<IFileDetailResponse> {
	const token = await getToken()
	const url = `${API_URL}files/${id}`
	try {
		return await client.get<IFileDetailResponse>(url, {
			headers: {
				Authorization: `access_token ${token}`,
			}
		})
	} catch (error) {
		console.error('Ошибка при запросе файлов:', error)
		throw error
	}
}
export async function sendFile(body: ICreateFile): Promise<ICreateFileResponse> {
	const token = await getToken()
	const url = `${API_URL}files/`

	try {
				return await client.post<ICreateFileResponse>(url, {
			headers: {
				Authorization: `access_token ${token}`,
			},
			body: body
		})
	} catch (error: any) {
		console.error('Ошибка при создании файла:', error)
		throw error
	}
}

export interface IDeleteFileResponse {
	success: boolean
	message?: string
	error?: string
}

export async function deleteFile(id: string): Promise<IDeleteFileResponse> {
	const token = await getToken()
	const url = `${API_URL}files/${id}`
	try {
		return await client.delete<IDeleteFileResponse>(url, {
			headers: {
				Authorization: `access_token ${token}`,
				'Content-Type': 'application/json',
			},
		})
	} catch (error: any) {
		console.error('Ошибка при удалении файла:', error)
		throw error
	}
}

export async function addTags(id: string, tags: string[]) {
	const token = await getToken()

	const url = `${API_URL}files/${id}/add_tags/`

	return await client.post(url, {
		headers: {
			Authorization: `access_token ${token}`,
		},
		body: { tags },
	})
}

export async function removeTags(id: string, tags: string[]) {
	const token = await getToken()

	const url = `${API_URL}files/${id}/remove_tags/`

	return await client.post(url, {
		headers: {
			Authorization: `access_token ${token}`,
		},
		body: { tags },
	})
}

export async function getTagList(page: number): Promise<ITagsListResponse> {
	const token = await getToken()

	const url = `${API_URL}tags/?page=${page}`

	return await client.get<ITagsListResponse>(url, {
		headers: {
			Authorization: `access_token ${token}`
		}
	})
}

export async function createTag(name: string): Promise<ITagResponse> {
	const token = await getToken()
	const url = `${API_URL}tags/`

	return client.post(url, {
		headers: {
			Authorization: `access_token ${token}`,
		},
		body: {name}
	})
}