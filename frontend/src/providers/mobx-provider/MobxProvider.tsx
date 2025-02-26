'use client'
import React, { createContext, ReactNode, useContext } from 'react';
import * as Stores from '../../store/index'; // Убедитесь, что ваш индексный файл корректен

// Определите интерфейс для контекста


// Создайте контекст с правильным типом
const StoreContext = createContext(Stores);

export const MobxProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    return (
        <StoreContext.Provider value={Stores}>
            {children}
        </StoreContext.Provider>
    );
};

// Пользовательский хук для доступа к сторам
export const useStore = () => {
    const context = useContext(StoreContext);
    if (!context) {
        throw new Error("useStore должен использоваться внутри MobxProvider");
    }
    return context;
};
