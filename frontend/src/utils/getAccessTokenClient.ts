import Cookies from "js-cookie";

export function getClientAccessToken() {
    return Cookies.get("accessToken") || null;
};
