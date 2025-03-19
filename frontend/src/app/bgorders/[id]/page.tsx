'use client' 
// TODO это будет серверный компонент
import { useParams } from 'next/navigation';
const OrderDetailBg  = () => {
  const params = useParams(); 
  const { id } = params; 

   return (
    <div>
   {id}
    </div>
  );
};
export default OrderDetailBg ;
