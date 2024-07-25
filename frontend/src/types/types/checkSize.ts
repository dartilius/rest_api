export const checkSize = (size: number | undefined) => {
  if (size !== undefined) {
    if (size / 1024 >= 1) {
      const formatted = Math.floor((size % 1048576) / 1000);

      return `${Math.floor(size / 1048576)}.${formatted} Mb`;
    } else {
      return `${Math.floor(size / 1024)} Kb`;
    }
  }
};
