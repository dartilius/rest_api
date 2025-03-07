import TabsPanel from "@/components/tabs/TabsPanel";
import { getDataBg } from "./api";

const OrdersPage = async ({ searchParams }: { searchParams?: {
   page: number;
   limit: number;
   name: string;
   status: string;
   timezone: string;
   version: string
} }) => {
   const { page = 1, limit = 10, name = "", status = "", timezone = "", version = "" } = await searchParams ?? {};
   const dataBg = await getDataBg({ page, limit, name, status, timezone, version });
   console.log(dataBg);
   return (

      <TabsPanel dataBg={dataBg}/>
 
  );
};
export default OrdersPage;
