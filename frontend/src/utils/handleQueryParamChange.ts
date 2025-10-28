export const handleQueryParamChange = (
    router: any,
    pathname: string,
    searchParams: URLSearchParams,
    paramName: string,
    value: string
) => {
    const params = new URLSearchParams(searchParams);

    if (value) {
        params.set(paramName, value);
        params.set('page', '1'); // сбрасываем страницу на 1
    } else {
        params.delete(paramName);
    }

   router.push(`${pathname}?${params.toString()}`);
};
