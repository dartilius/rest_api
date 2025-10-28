'use client'

import SelectTags from '@/app/files/components/SelectTags/SelectTags'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'

function SelectTagsFilterWrapper() {
	const searchParams = useSearchParams()
	const pathname = usePathname()
	const router = useRouter()

	const handleSelectTagsFile = (selectedTags: string[]) => {
		const params = new URLSearchParams(searchParams)

		params.delete('tags')

		selectedTags.forEach((tag) => {
			params.append('tags', tag)
		})

		params.set('page', '1')

		router.push(`${pathname}?${params.toString()}`)
	}

	return (
		<SelectTags
			label='Выбрать'
			onChange={(tags) => handleSelectTagsFile(tags.map((tag) => tag.name))}
			style={{ width: '100%' }}
		/>
	)
}

export default SelectTagsFilterWrapper
