// pages/login.tsx
"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Button,
  Card,
  CardBody,
  CardFooter,
  CardHeader,
  Input,
} from "@nextui-org/react";

import { AuthService } from "@/src/services/auth/auth.service";
import { toastError } from "@/src/utils/toast-error";

export default function LoginPage() {
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string>("");
  const router = useRouter();

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const response = await AuthService.login(email, password);

      if (response.status === 200) {
        router.push("/nomenclatures");
      } else {
        throw new Error("Не удалось выполнить вход");
      }
    } catch (error: Error | any) {
      toastError(`${error.response.status} ${error.response.statusText}`);
    }
  };

  return (
    <div className="flex flex-col h-screen justify-center items-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div style={{ textAlign: "center", width: "100%" }}>
            <p className="text-md">Авторизация</p>
          </div>
        </CardHeader>
        <CardBody className="space-y-4 gap-3">
          <div className="space-y-2">
            <label htmlFor="email">Email</label>
            <Input
              required
              id="email"
              placeholder="m@example.com"
              type="email"
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="password">Пароль</label>
            <Input
              required
              id="password"
              type="password"
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </CardBody>
        <CardFooter className="flex flex-col space-y-2 gap-3">
          <Button className="w-full" onClick={(e: any) => handleLogin(e)}>
            Login
          </Button>
          <Link className="text-sm text-center" href="#" prefetch={false}>
            Забыли пароль?
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
