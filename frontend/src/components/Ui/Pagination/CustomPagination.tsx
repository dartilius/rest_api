'use client'
import './customPagination.scss'
import { usePathname, useSearchParams, useRouter } from 'next/navigation'

const CustomPagination = ({
	totalItems,
	limit,
	page,
}: {
	totalItems: number
	limit: number
	page: number
}) => {
	const pathname = usePathname()
	const searchParams = useSearchParams()
	const router = useRouter()

	const currentPage = searchParams.get('page') || page
	const itemsPerPage = Number(searchParams.get('limit')) || limit

	const totalPages = Math.ceil(totalItems / itemsPerPage)

	const isNextButtonDisabled = Number(currentPage) >= totalPages

	const goToPage = (newPage: number) => {
		const params = new URLSearchParams(searchParams)
		params.set('page', newPage.toString())
		router.push(`${pathname}?${params.toString()}`)
	}

	return (
		<div className='w-full flex items-center justify-center gap-2 p-4'>
			<button
				onClick={() => goToPage(Number(currentPage) - 1)}
				disabled={Number(currentPage) === 1}
				className='px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300'
			>
				Предыдущая
			</button>
			<span className='text-black'>
				Страница: {Number(currentPage)} из {totalPages}
			</span>
			<button
				onClick={() => goToPage(Number(currentPage) + 1)}
				disabled={isNextButtonDisabled}
				className='px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300'
			>
				Следующая
			</button>
		</div>
	)
}

export default CustomPagination
