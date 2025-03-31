export const convertSizeFile = (size: number | undefined) => {
    if (size === undefined) return;

    if (size >= 1048576) {
        return `${(Math.ceil((size / 1048576) * 10) / 10).toFixed(1)} Mb`;
    } else {
        return `${Math.ceil(size / 1024)} Kb`;
    }
};
