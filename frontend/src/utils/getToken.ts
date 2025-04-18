import {getServerAccessToken} from "@/utils/getAccessTokenServer";
import {getClientAccessToken} from "@/utils/getAccessTokenClient";

export const getToken = async () => {
    const isSSR = typeof window === 'undefined'
    let token
    if (isSSR) {
        token = await getServerAccessToken()
    } else {
        token = getClientAccessToken()
    }

    return token
}