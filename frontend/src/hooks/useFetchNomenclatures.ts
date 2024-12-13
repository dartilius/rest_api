import {
  INomenclatureByIdResponse,
  INomenclatureResults,
  INomenclaturesService,
} from "@/interfaces/Nomenclatures.interface";
import NomenclaturesService from "@/services/NomenclaturesService";
import { useCallback, useEffect, useState } from "react";

// export const useFetchNomenclatures = ({
//   page,
//   limit,
//   token,
//   timezone,
//   status,
// }: INomenclaturesService) => {
//   const [nomenclaturesByPage, setNomenclaturesByPage] = useState<{
//     [key: number]: INomenclatureResults[];
//   }>({});
//   const [totalItems, setTotalItems] = useState<number>(0);
//   const [loading, setLoading] = useState<boolean>(true);

//   const fetchData = useCallback(async () => {
//     if (nomenclaturesByPage[page]) return; // Если данные для текущей страницы уже есть, пропускаем запрос

//     setLoading(true);

//     try {
//       const response = await NomenclaturesService.getAll({
//         token,
//         page,
//         limit,
//         timezone,
//         status,
//       });

//       setTimeout(() => {
//         setNomenclaturesByPage((prev) => ({
//           ...prev,
//           [page]: response.data.results, // Сохраняем данные для текущей страницы
//         }));
//         setTotalItems(response.data.count);
//         setLoading(false);
//       }, 1500);
//     } catch (error) {
//       console.error("Ошибка при загрузке данных:", error);
//       setLoading(false);
//     }
//   }, [page, limit, token, timezone, status, nomenclaturesByPage]);

//   useEffect(() => {
//     fetchData();
//   }, [page, limit, token, timezone, status, fetchData]);

//   // Возвращаем данные только для текущей страницы
//   const currentNomenclatures = nomenclaturesByPage[page] || [];

//   return {
//     nomenclatures: currentNomenclatures,
//     fetchData,
//     totalItems,
//     loading,
//   };
// };

export const useFetchNomenclatures = ({
  page,
  limit,
  token,
  timezone,
  status,
}: INomenclaturesService) => {
  const [nomenclaturesByPage, setNomenclaturesByPage] = useState<{
    [key: number]: INomenclatureResults[];
  }>({});
  const [totalItems, setTotalItems] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  const CACHE_KEY = "nomenclatures_cache";
  const CACHE_DURATION = 5 * 60 * 1000; // 5 минут в миллисекундах

  // Загружаем кэшированные данные из localStorage
  useEffect(() => {
    const cachedData = localStorage.getItem(CACHE_KEY);
    if (cachedData) {
      const { data, timestamp } = JSON.parse(cachedData);

      // Проверяем, не истёк ли срок действия кэша
      if (Date.now() - timestamp < CACHE_DURATION) {
        setNomenclaturesByPage(data.nomenclaturesByPage);
        setTotalItems(data.totalItems);
      } else {
        localStorage.removeItem(CACHE_KEY);
      }
    }
  }, []);

  const fetchData = useCallback(async () => {
    if (nomenclaturesByPage[page]) return; // Если данные для текущей страницы уже есть, пропускаем запрос

    setLoading(true);

    try {
      const response = await NomenclaturesService.getAll({
        token,
        page,
        limit,
        timezone,
        status,
      });

      const results = response.data.results;
      const totalCount = response.data.count;

      setTimeout(() => {
        // Обновляем состояние
        setNomenclaturesByPage((prev) => {
          const updatedData = { ...prev, [page]: results };

          // Сохраняем данные в localStorage
          localStorage.setItem(
            CACHE_KEY,
            JSON.stringify({
              data: {
                nomenclaturesByPage: updatedData,
                totalItems: totalCount,
              },
              timestamp: Date.now(),
            })
          );

          return updatedData;
        });

        setTotalItems(totalCount);
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error("Ошибка при загрузке данных:", error);
      setLoading(false);
    }
  }, [page, limit, token, timezone, status, nomenclaturesByPage]);

  useEffect(() => {
    fetchData();
  }, [fetchData, page]);

  const currentNomenclatures = nomenclaturesByPage[page] || [];

  return {
    nomenclatures: currentNomenclatures,
    fetchData,
    totalItems,
    loading,
  };
};

export const useFetchNomenclatureById = ({
  id,
  token,
}: {
  id: string | undefined;
  token: string | null;
}) => {
  const [nomenclature, setNomenclature] = useState<INomenclatureByIdResponse>();
  const [loading, setLoading] = useState<boolean>(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await NomenclaturesService.getById({
        token,
        id,
      });
      setTimeout(() => {
        setNomenclature(response.data);
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error("Ошибка при загрузке данных:", error);
    }
  }, [token, id]);

  useEffect(() => {
    fetchData();
  }, [id, token, fetchData]);

  return { nomenclature, fetchData, loading };
};
