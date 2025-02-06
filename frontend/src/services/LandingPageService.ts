import { API_URL_SECOND } from "@/config/api.config";
import axios from "axios";

class LandingPageService {
  private API_URL = API_URL_SECOND;
  getAllComment() {
    return axios.get(`${this.API_URL}comment`);
  }
}
