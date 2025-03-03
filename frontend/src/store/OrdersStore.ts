import { Dayjs } from 'dayjs';
import { action, makeObservable, observable } from 'mobx';
import { observer } from 'mobx-react';

// Интерфейс для типизации вашего стора
interface IOrdersStore {
  dataBg: any[];
  activeTab: number;
  startDate: Dayjs | null;
  endDate: Dayjs | null;
  setActiveTabs(val: number): void;
  setDataBg(data: any[]): void; 
}

class OrdersStore implements IOrdersStore {
  setNomenclatures(nomenclatures: any) {
     throw new Error("Method not implemented.");
  }
  dataBg: any[] = [];
  activeTab = 0;
  startDate: Dayjs | null = null;
  endDate: Dayjs | null = null;
  constructor() {
    makeObservable(this, {
      dataBg: observable,
      activeTab: observable,
      startDate: observable,
      endDate: observable,
      setActiveTabs: action,
      setStartDate: action,
      setEndDate: action,
      setDataBg: action,
    });
  }
  setDataBg(data: any[]): void {
    this.dataBg = data
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
