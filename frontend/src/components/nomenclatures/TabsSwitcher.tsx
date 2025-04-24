'use client'

import { useState, useEffect, ReactNode } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'

interface Props {
	mainTab: ReactNode
	settingsTab: ReactNode
	hardwareTab: ReactNode
}

type Tab = 'main' | 'settings' | 'hardware'

export default function TabsSwitcher({ mainTab, settingsTab, hardwareTab }: Props) {
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
		`px-4 py-2 rounded-t-md transition-colors ${
			activeTab === tab
				? 'bg-white text-blue-600 font-semibold'
				: 'bg-blue-700 text-white hover:bg-blue-600'
		}`

	return (
		<div>
			<div className='flex mb-4 space-x-2'>
				<button
					onClick={() => setActiveTab('main')}
					className={tabClass('main')}
				>
					Основная информация
				</button>
				<button
					onClick={() => setActiveTab('settings')}
					className={tabClass('settings')}
				>
					Настройки
				</button>
				<button
					onClick={() => setActiveTab('hardware')}
					className={tabClass('hardware')}
				>
					Информация о железе
				</button>
			</div>

			{activeTab === 'main' && mainTab}
			{activeTab === 'settings' && settingsTab}
			{activeTab === 'hardware' && hardwareTab}
		</div>
	)
}
