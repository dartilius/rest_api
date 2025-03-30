import { IDataPlayListsResponse } from '@/types/playListsTypes'
import { Dayjs } from 'dayjs'
import { action, computed, makeObservable, observable } from 'mobx'

// Интерфейс для типизации стора
interface IPlayListsStore {
  dataPlayLists: IDataPlayListsResponse | null
  page: number // Текущая страница для
  limit: number // Лимит на страницу
  totalCount: number // Общее количество элементов
  setData(data: IDataPlayListsResponse): void
  setPage(page: number): void // Установка текущей страницы
  setLimit(limit: number): void // Установка лимита
  setPagination(params: { page: number; limit: number }): void // Установка пагинации
  setTotalCount(count: number): void // Добавляем новый метод
  get totalPages(): number // Общее количество страниц
}

class PlayListsStore implements IPlayListsStore {
  dataPlayLists: IDataPlayListsResponse | null = null
  page = 1 // Начальная страница
  limit = 20 // Лимит по умолчанию
  totalCount = 0 // Общее количество элементов

  constructor() {
    makeObservable(this, {
      dataPlayLists: observable,
      page: observable,
      limit: observable,
      totalCount: observable,
      setData: action,
      setPage: action,
      setLimit: action,
      setPagination: action,
      setTotalCount: action,
      totalPages: computed, // Вычисляемое свойство для общего количества страниц 
    })
  }

  // Установка данных
  setData(data: IDataPlayListsResponse): void {
    this.dataPlayLists = data
  }

  // Установка текущей страницы
  setPage(page: number): void {
    this.page = page
  }

  // Установка лимита
  setLimit(limit: number): void {
    this.limit = limit
  }

  // Установка пагинации (страница и лимит)
  setPagination(params: { page: number; limit: number }): void {
    this.page = params.page
    this.limit = params.limit
  }

  setTotalCount(count: number): void {
    this.totalCount = count
  }
  // Вычисляемое свойство для общего количества страниц
  get totalPages(): number {
    return Math.ceil(this.totalCount / this.limit)
  }
}

const ordersStore = new PlayListsStore()
export default ordersStore
