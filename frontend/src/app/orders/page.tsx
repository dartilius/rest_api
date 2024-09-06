"use client";

import { useState } from "react";
import { Switch } from "@nextui-org/switch";

import AdOrders from "./ad/AdOrders";
import BgOrders from "./bg/BgOrders";

export default function AdOrdersPage() {
  const [changeOrdersList, setChangeOrdersList] = useState(false);

  return (
    <div className="flex flex-col gap-3">
      <Switch
        checked={changeOrdersList}
        onChange={() => setChangeOrdersList(!changeOrdersList)}
      >
        {changeOrdersList ? "Фоновые заказы" : "Рекламные заказы"}
      </Switch>
      {changeOrdersList ? <BgOrders /> : <AdOrders />}
    </div>
  );
}
