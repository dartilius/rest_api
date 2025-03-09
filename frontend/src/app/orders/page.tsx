import TabsPanel from "@/components/tabs/TabsPanel";
import { getDataAd, getDataBg } from "./api";

const OrdersPage = async ({ searchParams }: { searchParams?: {
   page: number;
   limit: number;
   name: string;
   status: string;
   timezone: string;
   version: string
} }) => {
   const { page = 1, limit = 10, name = "", status = "", timezone = "", version = "" } = searchParams ?? {};
   const dataBgResponse = await getDataBg({ page, limit, name, status, timezone, version });
   const dataAdResponse = await getDataAd({ page, limit, name, status, timezone, version });
   console.log(dataBgResponse);
   return (

      <TabsPanel dataBgResponse={dataBgResponse} dataAdResponse={dataAdResponse}/>
 
  );
};
export default OrdersPage;
