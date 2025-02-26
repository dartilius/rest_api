import { action, makeObservable, observable } from 'mobx';

// Интерфейс для типизации вашего стора
interface IOrdersStore {
  activeTab: number;
  setActiveTabs(val: number): void;
}

class OrdersStore implements IOrdersStore {
  activeTab: number = 0;

  constructor() {
    makeObservable(this, {
      activeTab: observable,
      setActiveTabs: action,
    });
  }

  setActiveTabs(val: number) {
    this.activeTab = val;
  }
}

const ordersStore = new OrdersStore();
export default ordersStore;
