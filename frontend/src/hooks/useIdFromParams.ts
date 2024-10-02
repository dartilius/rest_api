import { useParams } from "next/navigation";

const useIdFromParams = () => {
  const router = useParams();

  return router.id.toString();
};

export default useIdFromParams;
