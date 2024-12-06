import {
  INomenclatureByIdResponse,
  INomenclatureResults,
  INomenclaturesService,
} from "@/interfaces/Nomenclatures.interface";
import NomenclaturesService from "@/services/NomenclaturesService";
import { useEffect, useState } from "react";

export const useFetchNomenclatures = ({
  page,
  limit,
  token,
  timezone,
  status,
}: INomenclaturesService) => {
  const [nomenclatures, setNomenclatures] = useState<INomenclatureResults[]>(
    []
  );
  const [totalItems, setTotalItems] = useState<number>(0);

  const fetchData = async () => {
    setNomenclatures([]);
    const response = await NomenclaturesService.getAll({
      token: token,
      page: 1,
      limit: 5,
      timezone,
      status,
    });
    const newNomenclatures = response.data.results;
    const count = response.data.count;
    setTotalItems(count);
    setTimeout(() => setNomenclatures(newNomenclatures), 3000);
  };

  useEffect(() => {
    fetchData();
  }, [page, limit, token, timezone]);

  return { nomenclatures, fetchData, totalItems };
};

export const useFetchNomenclatureById = ({
  id,
  token,
}: {
  id: string | undefined;
  token: string | null;
}) => {
  const [nomenclature, setNomenclature] = useState<INomenclatureByIdResponse>();

  const fetchData = async () => {
    setNomenclature(undefined);
    if (!id || !token) return null;
    const response = await NomenclaturesService.getById({ id, token });
    setTimeout(() => setNomenclature(response.data), 3000);
  };

  useEffect(() => {
    fetchData();
  }, [id, token]);

  return { nomenclature, fetchData };
};
