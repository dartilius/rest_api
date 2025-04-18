'use client';

import { useState, ReactNode } from 'react';

interface Props {
    mainTab: ReactNode;
    settingsTab: ReactNode;
}

export default function TabsSwitcher({ mainTab, settingsTab }: Props) {
    const [activeTab, setActiveTab] = useState<'main' | 'settings'>('main');

    const tabClass = (tab: 'main' | 'settings') =>
        `px-4 py-2 rounded-t-md transition-colors ${
            activeTab === tab
                ? 'bg-white text-blue-600 font-semibold'
                : 'bg-blue-700 text-white hover:bg-blue-600'
        }`;

    return (
        <div>
            <div className="flex mb-4 space-x-2">
                <button onClick={() => setActiveTab('main')} className={tabClass('main')}>
                    Основная информация
                </button>
                <button onClick={() => setActiveTab('settings')} className={tabClass('settings')}>
                    Настройки
                </button>
            </div>

            {activeTab === 'main' && mainTab}
            {activeTab === 'settings' && settingsTab}
        </div>
    );
}
