import {
  INomenclatureByIdResponse,
  INomenclatureResults,
  INomenclaturesService,
} from "@/interfaces/Nomenclatures.interface";
import NomenclaturesService from "@/services/NomenclaturesService";
import { useCallback, useEffect, useState } from "react";

export const useFetchNomenclatures = ({
  page,
  limit,
  timezone,
  status,
}: INomenclaturesService) => {
  const [nomenclatures, setNomenclatures] = useState<INomenclatureResults[]>(
    []
  );
  const [totalItems, setTotalItems] = useState<number>(0);

  const fetchData = async () => {
    try {
      setNomenclatures([]);
      const response = await NomenclaturesService.getAll({
        page: page,
        limit: limit,
        timezone,
        status,
      });

      const newNomenclatures = response.data.results;
      const count = response.data.count;
      setTotalItems(count);
      setTimeout(() => setNomenclatures(newNomenclatures), 3000);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, limit, timezone]);

  return { nomenclatures, fetchData, totalItems };
};

export const useFetchNomenclatureById = (id: string | undefined) => {
  const [nomenclature, setNomenclature] = useState<INomenclatureByIdResponse>();
  const [loading, setLoading] = useState<boolean>(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await NomenclaturesService.getById(id);
      setTimeout(() => {
        setNomenclature(response.data);
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error("Ошибка при загрузке данных:", error);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [id, fetchData]);

  return { nomenclature, fetchData, loading };
};
