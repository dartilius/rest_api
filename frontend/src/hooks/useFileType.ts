export const useGetFileMimeType = (fileName: string) => {
        const extension = fileName.split(".").pop();

        switch (extension) {
            case "mp3":
                return "mp3";
            case "wav":
                return "wav";
            case "png":
                return "png";
            case "jpg":
            case "jpeg":
                return "jpeg";
            case "gif":
                return "gif";
            case "pdf":
                return "application/pdf";
            default:
                return "application/octet-stream";
        }

};
