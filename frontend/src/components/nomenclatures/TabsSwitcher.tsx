'use client'

import { useState, useEffect, ReactNode } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

interface Props {
	mainTab: ReactNode
	settingsTab: ReactNode
	hardwareTab: ReactNode
	statisticsTab: ReactNode
}

type Tab = 'main' | 'settings' | 'hardware' | 'statistics'

export default function TabsSwitcher({ mainTab, settingsTab, hardwareTab, statisticsTab }: Props) {
	const searchParams = useSearchParams()
	const router = useRouter()

	const initialTab = (searchParams.get('tab') as Tab) || 'main'
	const [activeTab, setActiveTab] = useState<Tab>(initialTab)

	useEffect(() => {
		const current = new URLSearchParams(Array.from(searchParams.entries()))
		current.set('tab', activeTab)
		const newUrl = `?${current.toString()}`
		router.replace(newUrl)
	}, [activeTab])

	const tabClass = (tab: Tab) =>
		`px-3 sm:px-4 py-2.5 sm:py-2 text-base sm:text-base rounded-t-md transition-colors whitespace-nowrap overflow-hidden text-ellipsis max-w-[150px] sm:max-w-none ${
			activeTab === tab
				? 'bg-white text-blue-600 font-semibold'
				: 'bg-blue-700 text-white hover:bg-blue-600'
		}`

	return (
		<div>
			<div className='flex mb-2 sm:mb-4 space-x-2 overflow-x-auto custom_scroll pb-2 px-1'>
				<button
					onClick={() => setActiveTab('main')}
					className={tabClass('main')}
					title='Основная информация'
				>
					Основная информация
				</button>
				<button
					onClick={() => setActiveTab('settings')}
					className={tabClass('settings')}
					title='Настройки'
				>
					Настройки
				</button>
				<button
					onClick={() => setActiveTab('hardware')}
					className={tabClass('hardware')}
					title='Информация о железе'
				>
					Информация о железе
				</button>
				<button
					onClick={() => setActiveTab('statistics')}
					className={tabClass('statistics')}
					title='Статистика'
				>
					Статистика
				</button>
			</div>

			{activeTab === 'main' && mainTab}
			{activeTab === 'settings' && settingsTab}
			{activeTab === 'hardware' && hardwareTab}
			{activeTab === 'statistics' && statisticsTab}
		</div>
	)
}
