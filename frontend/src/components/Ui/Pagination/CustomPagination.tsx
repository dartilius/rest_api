'use client'
import { usePathname, useRouter, useSearchParams } from 'next/navigation'
import { RefObject } from 'react'
import CustomPaginationDesktop from './CustomPaginationDesktop'
import CustomPaginationMobile from './CustomPaginationMobile'

const CustomPagination = ({
	totalItems,
	topRef,
	isMobile,
}: {
	totalItems: number
	topRef: RefObject<HTMLDivElement>
	isMobile: boolean
}) => {
	const pathname = usePathname()
	const searchParams = useSearchParams()
	const router = useRouter()
	const currentPage = Number(searchParams.get('page') || 1)
	const itemsPerPage = Number(searchParams.get('limit')) || 20

	const totalPages = Math.ceil(totalItems / itemsPerPage)

	const isNextButtonDisabled = Number(currentPage) >= totalPages

	const scrollToTop = () => {
		topRef.current?.scrollIntoView({ behavior: 'smooth' })
	}

	const goToPage = (newPage: number) => {
		const params = new URLSearchParams(searchParams)
		params.set('page', newPage.toString())
		router.push(`${pathname}?${params.toString()}`)
	}

	const nextPage = () => {
		goToPage(currentPage + 1)
		scrollToTop()
	}

	const prevPage = () => {
		goToPage(currentPage - 1)
		scrollToTop()
	}

	const isPrevButtonDisabled = currentPage === 1
	const goToFirstPage = () => {
		goToPage(1)
		scrollToTop()
	}

	return (
		<div className='flex items-center justify-center p-1'>
			{isMobile ? (
				<CustomPaginationMobile
					currentPage={Number(currentPage)}
					totalPages={totalPages}
					prevPage={prevPage}
					nextPage={nextPage}
					isNextButtonDisabled={isNextButtonDisabled}
					isPrevButtonDisabled={isPrevButtonDisabled}
					goToFirstPage={goToFirstPage}
				/>
			) : (
				<CustomPaginationDesktop
					currentPage={Number(currentPage)}
					totalPages={totalPages}
					prevPage={prevPage}
					nextPage={nextPage}
					isNextButtonDisabled={isNextButtonDisabled}
					isPrevButtonDisabled={isPrevButtonDisabled}
					goToFirstPage={goToFirstPage}
				/>
			)}
		</div>
	)
}

export default CustomPagination
