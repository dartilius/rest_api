import { IDataAdResponse, IDataBgResponse } from '@/types/orderTypes';
import { Dayjs } from 'dayjs';
import { action, makeObservable, observable } from 'mobx';


// Интерфейс для типизации вашего стора
interface IOrdersStore {
  dataBgResponse: IDataBgResponse | null;
  dataAdResponse: IDataAdResponse | null;
  activeTab: number;
  startDate: Dayjs | null;
  endDate: Dayjs | null;
  setActiveTabs(val: number): void;
  setDataBg(data: IDataBgResponse): void; 
  setDataAd(data: IDataAdResponse): void; 
}

class OrdersStore implements IOrdersStore {
  setNomenclatures(nomenclatures: any) {
     throw new Error("Method not implemented.");
  }
  dataBgResponse: IDataBgResponse | null = null;
  dataAdResponse: IDataAdResponse | null = null;
  activeTab = 0;
  startDate: Dayjs | null = null;
  endDate: Dayjs | null = null;
  constructor() {
    makeObservable(this, {
      dataBgResponse: observable,
      dataAdResponse: observable,
      activeTab: observable,
      startDate: observable,
      endDate: observable,
      setActiveTabs: action,
      setStartDate: action,
      setEndDate: action,
      setDataBg: action,
      setDataAd: action,
    });
  }
  setDataBg(data: IDataBgResponse): void {
    this.dataBgResponse = data
  }
  setDataAd(data: IDataAdResponse): void {
    this.dataAdResponse = data
  }
  setActiveTabs(val: number) {
    this.activeTab = val;
  }
  setStartDate(date: Dayjs | null) {
    this.startDate = date;
  }

  setEndDate(date: Dayjs | null) {
    this.endDate = date;
  }

  get dateRange() {
    return { startDate: this.startDate, endDate: this.endDate };
  }
}

const ordersStore = new OrdersStore();
export default ordersStore;
