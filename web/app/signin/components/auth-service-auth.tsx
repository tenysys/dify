'use client'

import { Button } from '@langgenius/dify-ui/button'
import { Lock01 } from '@/app/components/base/icons/src/vender/solid/security'
import {
  AUTH_SERVICE_ENABLED,
  AUTH_SERVICE_LOGIN_LABEL,
  AUTH_SERVICE_LOGIN_URL,
  AUTH_SERVICE_REDIRECT_PARAM,
  AUTH_SERVICE_TOKEN_PARAM,
} from '@/config'
import { useSearchParams } from '@/next/navigation'
import { basePath } from '@/utils/var'

const CALLBACK_PATH = '/signin/auth-service'
const REDIRECT_URI_PLACEHOLDER = '{redirect_uri}'

const buildCallbackUrl = (searchParams: URLSearchParams) => {
  const callbackUrl = new URL(`${globalThis.location.origin}${basePath}${CALLBACK_PATH}`)
  searchParams.delete(AUTH_SERVICE_TOKEN_PARAM)
  searchParams.delete('access_token')
  callbackUrl.search = searchParams.toString()
  return callbackUrl.toString()
}

const buildAuthServiceLoginUrl = (callbackUrl: string) => {
  const loginUrl = AUTH_SERVICE_LOGIN_URL.trim()
  if (loginUrl.includes(REDIRECT_URI_PLACEHOLDER))
    return loginUrl.replaceAll(REDIRECT_URI_PLACEHOLDER, encodeURIComponent(callbackUrl))

  const url = new URL(loginUrl, globalThis.location.origin)
  url.searchParams.set(AUTH_SERVICE_REDIRECT_PARAM, callbackUrl)
  return url.toString()
}

export default function AuthServiceAuth() {
  const searchParams = useSearchParams()

  if (!AUTH_SERVICE_ENABLED || !AUTH_SERVICE_LOGIN_URL)
    return null

  const handleClick = () => {
    const callbackUrl = buildCallbackUrl(new URLSearchParams(searchParams.toString()))
    globalThis.location.href = buildAuthServiceLoginUrl(callbackUrl)
  }

  return (
    <Button
      tabIndex={0}
      onClick={handleClick}
      className="w-full"
    >
      <Lock01 className="mr-2 size-5 text-text-accent-light-mode-only" />
      <span className="truncate">{AUTH_SERVICE_LOGIN_LABEL}</span>
    </Button>
  )
}
