export const createModalURL = (pathname: string, searchParams: URLSearchParams, isOpen: boolean) => {
    const params = new URLSearchParams(searchParams);
    if (isOpen) {
        params.set('openModal', 'true');
    } else {
        params.delete('openModal');
    }
    return `${pathname}?${params.toString()}`;
};


