import { IAuthInput } from "@/src/types/interface/user.interface";

export interface IUserState {
  email: string;
}

export interface ITokens {
  access: string;
  refresh: string;
}

export interface IIinitialState {
  user: IUserState | null;
  isLoading: boolean;
}

export interface IEmailPassword {
  email: string;
  password: string;
}

export interface IAuthResponse extends ITokens {
  user: IAuthInput;
}
