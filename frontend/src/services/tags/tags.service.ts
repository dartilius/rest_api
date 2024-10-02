//TODO: Переписать на классы

import { API_URL } from "@/src/config/api.config";
import {
  TagsListInterface,
} from "@/src/types/interface/tags.interface";
import axios from "axios";

class TagsService {
  private URL = `${API_URL}/tags/`;

  getAll() {
    return axios.get<TagsListInterface>(`${this.URL}`);
  }
}

export default new TagsService()