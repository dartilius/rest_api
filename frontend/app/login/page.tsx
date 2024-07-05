// pages/login.tsx
"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@nextui-org/button";

import styles from "./Login.module.scss";

import { AuthService } from "../../services/auth/auth.service";

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
      setError(error.response?.data?.message || "Ошибка при входе");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.container_left} />
      <div className={styles.container_right}>
        <form className={styles.container_right_login} onSubmit={handleLogin}>
          <h1 className={styles.container_right_login_title}>Вход</h1>
          <div className={styles.container_right_login_email}>
            <p className={styles.container_right_login_email_label}>Email</p>
            <input
              required
              className={styles.container_right_login_email_input}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className={styles.container_right_login_password}>
            <p className={styles.container_right_login_password_label}>
              Пароль
            </p>
            <input
              required
              className={styles.container_right_login_password_input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <Button
            className={styles.container_right_login_button}
            color="primary"
            type="submit"
          >
            <p className={styles.container_right_login_button_text}>Войти</p>
          </Button>
          {error && <p>{error}</p>}
        </form>
      </div>
    </div>
  );
}
