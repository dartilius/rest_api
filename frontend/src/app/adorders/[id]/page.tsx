'use client' 
// TODO это будет серверный компонент
import { useParams } from 'next/navigation';
const OrderDetailAd  = () => {
  const params = useParams(); 
  const { id } = params; 

   return (
    <div>
   {id}
    </div>
  );
};
export default OrderDetailAd ;