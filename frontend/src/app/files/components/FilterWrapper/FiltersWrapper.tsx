import { ModalAddFile } from '@/app/files/components/ModalAddFile/ModalAddFile'
import SelectTagsFilterWrapper from '@/app/files/components/SelectTags/SelectTagsFilterWrapper'
import SelectType from '@/app/files/components/SelectType/SelectType'
import { Search } from '@/components/nomenclatures'

const FiltersWrapper = () => {
	return (
		<div className='flex flex-row gap-2 w-full p-4'>
			<Search
				nameQueryParams='name'
				label='Название'
			/>
			<SelectType />
			<SelectTagsFilterWrapper />
			<ModalAddFile />
		</div>
	)
}

export default FiltersWrapper
