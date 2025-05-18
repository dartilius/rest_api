type CustomPaginationDesktopProps = {
	currentPage: number
	totalPages: number
	prevPage: () => void
	nextPage: () => void
	isNextButtonDisabled: boolean
	isPrevButtonDisabled: boolean
	goToFirstPage: () => void
}
export default function CustomPaginationDesktop({
	currentPage,
	totalPages,
	prevPage,
	nextPage,
	isNextButtonDisabled,
	isPrevButtonDisabled,
	goToFirstPage,
}: CustomPaginationDesktopProps) {
	return (
		<div className='w-full flex items-center justify-center gap-2 p-4'>
			<button
				onClick={prevPage}
				disabled={isPrevButtonDisabled}
				className='px-4 py-2 bg-info text-white rounded disabled:bg-gray-300'
			>
				Предыдущая
			</button>
			<span className='text-black'>
				Страница: {Number(currentPage)} из {totalPages}
			</span>
			<button
				onClick={nextPage}
				disabled={isNextButtonDisabled}
				className='px-4 py-2 bg-info text-white rounded disabled:bg-gray-300'
			>
				Следующая
			</button>
			<button
				className='px-4 py-2 bg-info text-white rounded disabled:bg-gray-300'
				onClick={goToFirstPage}
				disabled={isPrevButtonDisabled}
			>
				На первую страницу
			</button>
		</div>
	)
}
