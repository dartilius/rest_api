import { IDataAdResponse, IDataBgResponse } from '@/types/orderTypes';
import { Dayjs } from 'dayjs';
import { action, computed, makeObservable, observable } from 'mobx';

// Интерфейс для типизации стора
interface IOrdersStore {
  dataBgResponse: IDataBgResponse | null;
  dataAdResponse: IDataAdResponse | null;
  activeTab: number;
  page: number; // Текущая страница для 

  limit: number; // Лимит на страницу
  totalCountBg: number; // Общее количество элементов для Bg-Orders
  totalCountAd: number; // Общее количество элементов для Ad-Orders
  setActiveTabs(val: number): void;
  setDataBg(data: IDataBgResponse): void;
  setDataAd(data: IDataAdResponse): void;
  setPage(page: number): void; // Установка текущей страницы 
  setLimit(limit: number): void; // Установка лимита
  setPagination(params: { page: number; limit: number }): void; // Установка пагинации
  get totalPagesBg(): number; // Общее количество страниц для Bg-Orders
  get totalPagesAd(): number; // Общее количество страниц для Ad-Orders
}

class OrdersStore implements IOrdersStore {
  dataBgResponse: IDataBgResponse | null = null;
  dataAdResponse: IDataAdResponse | null = null;
  activeTab = 0;
  page = 1; // Начальная страница
  limit = 20; // Лимит по умолчанию
  totalCountBg = 0; // Общее количество элементов для Bg-Orders
  totalCountAd = 0; // Общее количество элементов для Ad-Orders

  constructor() {
    makeObservable(this, {
      dataBgResponse: observable,
      dataAdResponse: observable,
      activeTab: observable,
      page: observable,
      limit: observable,
      totalCountBg: observable,
      totalCountAd: observable,
      setActiveTabs: action,
      setDataBg: action,
      setDataAd: action,
      setPage: action,
      setLimit: action,
      setPagination: action,
      totalPagesBg: computed, // Вычисляемое свойство для общего количества страниц Bg-Orders
      totalPagesAd: computed, // Вычисляемое свойство для общего количества страниц Ad-Orders
    });
  }

  // Установка данных для Bg-заказов
  setDataBg(data: IDataBgResponse): void {
    this.dataBgResponse = data;
  }

  // Установка данных для Ad-заказов
  setDataAd(data: IDataAdResponse): void {
    this.dataAdResponse = data;
  }

  // Установка активной вкладки
  
  setActiveTabs(val: number){
    this.activeTab = val;
  }

  // Установка текущей страницы
  setPage(page: number): void {
    this.page = page;
  }

  // Установка лимита
  setLimit(limit: number): void {
    this.limit = limit;
  }

  // Установка пагинации (страница и лимит)
  setPagination(params: { page: number;  limit: number }): void {
    this.page = params.page;
    this.limit = params.limit;
  }


   // Вычисляемое свойство для общего количества страниц Bg-Orders
   get totalPagesBg(): number {
    return Math.ceil(this.totalCountBg / this.limit);
  }

  // Вычисляемое свойство для общего количества страниц Ad-Orders
  get totalPagesAd(): number {
    return Math.ceil(this.totalCountAd / this.limit);
  }
}

const ordersStore = new OrdersStore();
export default ordersStore;