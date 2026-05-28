import {
  CONSOLE_ACCESS_TOKEN_LOCAL_STORAGE_NAME,
  CONSOLE_CSRF_TOKEN_LOCAL_STORAGE_NAME,
  CONSOLE_REFRESH_TOKEN_LOCAL_STORAGE_NAME,
} from '@/config'

export type ConsoleAuthTokens = {
  access_token?: string
  refresh_token?: string
  csrf_token?: string
}

export const getConsoleAccessToken = () => globalThis.localStorage.getItem(CONSOLE_ACCESS_TOKEN_LOCAL_STORAGE_NAME) || ''

export const getConsoleRefreshToken = () => globalThis.localStorage.getItem(CONSOLE_REFRESH_TOKEN_LOCAL_STORAGE_NAME) || ''

export const getConsoleCsrfToken = () => globalThis.localStorage.getItem(CONSOLE_CSRF_TOKEN_LOCAL_STORAGE_NAME) || ''

export const storeConsoleAuthTokens = (tokens?: ConsoleAuthTokens) => {
  if (!tokens)
    return

  if (tokens.access_token)
    globalThis.localStorage.setItem(CONSOLE_ACCESS_TOKEN_LOCAL_STORAGE_NAME, tokens.access_token)
  if (tokens.refresh_token)
    globalThis.localStorage.setItem(CONSOLE_REFRESH_TOKEN_LOCAL_STORAGE_NAME, tokens.refresh_token)
  if (tokens.csrf_token)
    globalThis.localStorage.setItem(CONSOLE_CSRF_TOKEN_LOCAL_STORAGE_NAME, tokens.csrf_token)
}

export const clearConsoleAuthTokens = () => {
  globalThis.localStorage.removeItem(CONSOLE_ACCESS_TOKEN_LOCAL_STORAGE_NAME)
  globalThis.localStorage.removeItem(CONSOLE_REFRESH_TOKEN_LOCAL_STORAGE_NAME)
  globalThis.localStorage.removeItem(CONSOLE_CSRF_TOKEN_LOCAL_STORAGE_NAME)
}
