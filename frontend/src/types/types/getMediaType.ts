export  const getMediaType = (name: string | undefined) => {
    if (!name) return undefined;
    const extension = name.split('.').pop()?.toLowerCase()
    if (['mp3', 'wav', 'ogg'].includes(extension!)) {
        return 'audio';
    } else if (['mp4', 'webm', 'ogg', 'mov'].includes(extension!)) {
        return 'video';
    } else if (['png', 'jpg'].includes(extension!)) {
        return 'image';
    }
    // return null; // Unknown type
};